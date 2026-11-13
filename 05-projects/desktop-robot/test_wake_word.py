import tempfile
import unittest
import wave
import queue
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import numpy as np

from wake_word import load_acknowledgement


class CaptureWatchdogTests(unittest.TestCase):
    @contextmanager
    def source(self, enter=None, channels=1):
        from wake_word import microphone_frames
        stream = Mock(active=True, stopped=False, closed=False)
        callbacks = {}
        def create(**kwargs):
            callbacks.update(kwargs)
            def begin():
                if enter is not None:
                    enter(callbacks, stream)
                return stream
            stream.__enter__ = Mock(side_effect=begin)
            stream.__exit__ = Mock(return_value=False)
            return stream
        with patch('sounddevice.InputStream', side_effect=create), \
             patch('robot.device_format', return_value=(16000, channels)):
            frames = microphone_frames(0)
            try:
                yield frames, stream, callbacks
            finally:
                frames.close()

    @staticmethod
    def send(callbacks, value=0., channels=1, overflow=False):
        callbacks['callback'](np.full((640, channels), value, dtype='float32'), 640,
                              None, SimpleNamespace(input_overflow=overflow))

    def test_inactive_or_stopped_or_closed_device_raises_and_cleans_up(self):
        for attribute, value in [('active', False), ('stopped', True), ('closed', True)]:
            with self.subTest(attribute=attribute):
                def enter(callbacks, stream):
                    setattr(stream, attribute, value)
                with self.source(enter) as (frames, stream, _):
                    with self.assertRaisesRegex(RuntimeError, 'stopped or became inactive'):
                        next(frames)
                    stream.__exit__.assert_called_once()

    def test_finished_callback_is_observed_even_before_stream_flags_update(self):
        with self.source(lambda callbacks, stream: callbacks['finished_callback']()) as (frames, stream, _):
            with self.assertRaisesRegex(RuntimeError, 'stopped or became inactive'):
                next(frames)
            stream.__exit__.assert_called_once()

    def test_callback_exception_reaches_consumer_instead_of_silent_queue_wait(self):
        import sounddevice as sd
        def enter(callbacks, stream):
            broken = Mock()
            broken.copy.side_effect = ValueError('broken input frame')
            # PortAudio catches CallbackAbort rather than forwarding it.
            with self.assertRaises(sd.CallbackAbort):
                callbacks['callback'](broken, 640, None, SimpleNamespace(input_overflow=False))
            stream.active = False
        with self.source(enter) as (frames, stream, _):
            with self.assertRaisesRegex(RuntimeError, 'callback failed: ValueError: broken input frame'):
                next(frames)
            stream.__exit__.assert_called_once()

    def test_active_stream_without_callbacks_expires_with_bounded_queue_polls(self):
        from wake_word import CAPTURE_NO_FRAME_SECONDS, CAPTURE_POLL_SECONDS
        now = [0.]
        timeouts = []
        class EmptyQueue(queue.Queue):
            def get(self, block=True, timeout=None):
                if not block:
                    return super().get(block=False)
                timeouts.append(timeout)
                now[0] += timeout
                raise queue.Empty
        # Stream/device opening time does not consume the first-frame grace.
        def enter(callbacks, stream):
            now[0] = 10.
        with patch('queue.Queue', EmptyQueue), patch('time.monotonic', side_effect=lambda: now[0]), \
             self.source(enter) as (frames, stream, _):
            with self.assertRaisesRegex(RuntimeError, 'watchdog: no microphone frames'):
                next(frames)
            self.assertEqual(now[0], 10 + CAPTURE_NO_FRAME_SECONDS)
            self.assertTrue(all(0 < timeout <= CAPTURE_POLL_SECONDS for timeout in timeouts))
            stream.__exit__.assert_called_once()

    def test_silence_callbacks_refresh_liveness_for_long_standby(self):
        now = [0.]
        with patch('time.monotonic', side_effect=lambda: now[0]), \
             self.source(lambda callbacks, stream: self.send(callbacks)) as (frames, stream, callbacks):
            audio, overflow = next(frames)
            np.testing.assert_array_equal(audio, np.zeros(640, dtype='float32'))
            self.assertFalse(overflow)
            for _ in range(200):
                now[0] += .04
                self.send(callbacks)
                audio, overflow = next(frames)
                self.assertEqual(audio.shape, (640,))
                self.assertFalse(overflow)
            self.assertGreater(now[0], 1.5)
            stream.__exit__.assert_not_called()
        stream.__exit__.assert_called_once()

    def test_queue_overflow_keeps_bounded_audio_and_discontinuity_flag(self):
        def enter(callbacks, stream):
            for index in range(26):
                self.send(callbacks, index / 100, channels=2)
        with self.source(enter, channels=2) as (frames, _, _):
            output = [next(frames) for _ in range(25)]
            self.assertTrue(all(audio.shape == (640,) for audio, _ in output))
            self.assertAlmostEqual(float(output[0][0][0]), .01)
            self.assertAlmostEqual(float(output[-1][0][0]), .25)
            self.assertTrue(output[-1][1])

    def test_hardware_overflow_flag_and_generator_close_are_preserved(self):
        with self.source(lambda callbacks, stream: self.send(callbacks, overflow=True)) as (frames, stream, _):
            self.assertTrue(next(frames)[1])
            frames.close()
            stream.__exit__.assert_called_once()


class WakeTests(unittest.TestCase):
    def test_optional_confirmation_is_preloaded_without_changing_default(self):
        from wake_word import SenseVoiceWake
        primary, fallback = Mock(), Mock()
        with patch('sherpa_onnx.OfflineRecognizer.from_sense_voice',
                   side_effect=[primary, fallback]) as create:
            default = SenseVoiceWake(Path('assets'), .005)
            self.assertIs(default.recognizer, primary)
            self.assertIsNone(default.confirmation_recognizer)
            self.assertEqual(create.call_count, 1)
            self.assertEqual(create.call_args.kwargs['language'], 'ja')
            self.assertEqual(create.call_args.kwargs['num_threads'], 2)
        with patch('sherpa_onnx.OfflineRecognizer.from_sense_voice',
                   side_effect=[primary, fallback]) as create:
            candidate = SenseVoiceWake(Path('assets'), .005, confirmation='auto-consensus')
            self.assertIs(candidate.confirmation_recognizer, fallback)
            self.assertEqual([call.kwargs['language'] for call in create.call_args_list],
                             ['ja', 'auto'])
            self.assertTrue(all(call.kwargs['num_threads'] == 2 for call in create.call_args_list))

    def test_confirmation_load_failure_preserves_primary_and_rejects_retry(self):
        from wake_word import SenseVoiceWake
        with patch('sherpa_onnx.OfflineRecognizer.from_sense_voice',
                   side_effect=[Mock(), RuntimeError('not enough memory')]):
            wake = SenseVoiceWake(Path('assets'), .005, confirmation='auto-consensus')
        self.assertTrue(wake.confirm('Naruto', None)['accepted'])
        capture = SimpleNamespace(state='done', start_sample=100,
                                  end_sample=16100, last_voice_sample=8100)
        result = wake.confirm('なるほ', np.zeros(16000), capture)
        self.assertFalse(result['accepted'])
        self.assertIn('not enough memory', result['error'])

    def test_capture_result_is_available_only_on_the_completed_frame(self):
        from wake_word import WakeUtterances
        gate = WakeUtterances(.005)
        self.assertIsNone(gate.last_result)
        audio = None
        for block in [np.zeros(640)] * 5 + [np.full(640, .02)] * 8 + [np.zeros(640)] * 14:
            candidate = gate.feed(block)
            if candidate is not None:
                audio = candidate
        self.assertIsNotNone(audio)
        self.assertIs(gate.last_result.samples, audio)
        self.assertEqual(gate.last_result.end_sample - gate.last_result.start_sample,
                         len(audio))
        self.assertGreater(gate.last_result.last_voice_sample - gate.last_result.start_sample, 0)
        gate.feed(np.zeros(640))
        self.assertIsNone(gate.last_result)
        self.assertIsNone(WakeUtterances(.005).last_result)

    def test_confirmation_rejects_mismatched_capture_bounds(self):
        from wake_word import SenseVoiceWake
        wake = SenseVoiceWake.__new__(SenseVoiceWake)
        wake.confirmation = 'auto-consensus'
        wake.recognize_confirmation = Mock(return_value='Naruto')
        for capture in [None, SimpleNamespace(state='done'),
                        SimpleNamespace(state='done', start_sample=0,
                                        end_sample=100, last_voice_sample=50),
                        SimpleNamespace(state='done', start_sample=-1,
                                        end_sample=15999, last_voice_sample=8000)]:
            with self.subTest(capture=capture):
                result = wake.confirm('なるほ', np.zeros(16000), capture)
                self.assertFalse(result['accepted'])
                self.assertIn('error', result)
        wake.recognize_confirmation.assert_not_called()

    def test_discontinuity_clears_partial_capture_before_confirmation(self):
        from wake_word import SenseVoiceWake
        wake = SenseVoiceWake.__new__(SenseVoiceWake)
        wake.threshold = .005
        wake.confirmation = 'auto-consensus'
        wake.recognize = Mock(return_value='なるほ')
        wake.recognize_confirmation = Mock(side_effect=['なると', 'Naruto', 'なるほど'])
        closed = []
        def frames(device):
            try:
                for block in [np.zeros(640)] * 5 + [np.full(640, .02)] * 5:
                    yield block, False
                yield np.zeros(640), True
                for block in ([np.zeros(640)] * 15 + [np.full(640, .02)] * 8
                              + [np.zeros(640)] * 14):
                    yield block, False
            finally:
                closed.append(True)
        with patch('wake_word.microphone_frames', side_effect=frames):
            self.assertEqual(wake.wait(0), 'Naruto')
        wake.recognize.assert_called_once()
        self.assertEqual(wake.recognize_confirmation.call_count, 3)
        self.assertTrue(closed)

    def test_wake_and_chat_capture_settings_are_independent(self):
        from robot import serve_conversations
        args = SimpleNamespace(auto_listen=True, ready_file=None, language='zh',
                               prompt_mode='original', first_clause_chars=16,
                               input_device=0, output_device=3, threshold=.02,
                               silence=.7, metrics=None, wake_backend='sensevoice',
                               wake_model=None, wake_ack=Path('ikuzo.wav'), assets=Path('assets'),
                               wake_threshold=.005, wake_min_voice_ms=120,
                               wake_preroll_ms=200, wake_silence=.56,
                               min_voice_ms=200, preroll_ms=500)
        wake = Mock()
        wake.wait.side_effect = KeyboardInterrupt
        with patch('wake_word.SenseVoiceWake', return_value=wake) as create, \
             patch('wake_word.load_acknowledgement', return_value=(np.ones(32), 24000)), \
             patch('robot.play_audio'), patch('robot.notify_ready'):
            with self.assertRaises(KeyboardInterrupt):
                serve_conversations(args, Mock(), Mock(), None)
        create.assert_called_once_with(Path('assets'), .005, 120, 200, .56, confirmation='none')

    def test_proper_name_matches_but_ordinary_phrases_do_not(self):
        from wake_word import is_naruto
        for text in ('Naruto!', 'ＮＡＲＵＴＯ', 'なると。', 'ナルト', 'なるど。', 'なるとなると。'):
            self.assertTrue(is_naruto(text), text)
        for text in ('', 'なるほど', 'なるほ', '然后', '南图', '如托', 'Naruto是什么',
                     'Notto', 'I like Naruto', 'ナルトについて教えて'):
            self.assertFalse(is_naruto(text), text)

    def test_gate_rejects_quiet_audio_and_short_spikes(self):
        from wake_word import WakeUtterances
        gate = WakeUtterances(.005)
        for audio in [np.zeros(640)] * 50 + [np.ones(640)] + [np.zeros(640)] * 50:
            self.assertIsNone(gate.feed(audio))

    def test_gate_preserves_word_and_rejects_long_speech(self):
        from wake_word import WakeUtterances
        gate = WakeUtterances(.005)
        results = []
        for audio in [np.zeros(640)]*5 + [np.ones(640)*.02]*8 + [np.zeros(640)]*15:
            result = gate.feed(audio)
            if result is not None:
                results.append(result)
        self.assertEqual(len(results), 1)
        self.assertEqual(np.count_nonzero(results[0]), 8*640)
        for audio in [np.ones(640)*.02]*100 + [np.zeros(640)]*15:
            self.assertIsNone(gate.feed(audio))

    def test_speech_backend_rejects_near_word_before_accepting_name(self):
        from wake_word import SenseVoiceWake
        gate = SenseVoiceWake.__new__(SenseVoiceWake)
        gate.threshold = .005
        gate.recognize = Mock(side_effect=['なるほど。', 'なると。'])
        closed = []
        def frames(device):
            try:
                for _ in range(2):
                    for audio in [np.zeros(640)]*5 + [np.ones(640)*.02]*8 + [np.zeros(640)]*15:
                        yield audio, False
            finally:
                closed.append(True)
        with patch('wake_word.microphone_frames', side_effect=frames):
            self.assertEqual(gate.wait(0), 'Naruto')
        self.assertEqual(gate.recognize.call_count, 2)
        self.assertTrue(closed)

    def test_callback_capture_feeds_keyword_model_without_blocking_reads(self):
        from wake_word import NarutoWake
        gate = NarutoWake.__new__(NarutoWake)
        gate.kws = Mock()
        gate.kws.is_ready.return_value = True
        gate.kws.get_result.return_value = 'Naruto'
        context = Mock()
        context.__exit__ = Mock(return_value=False)
        context.active, context.stopped, context.closed = True, False, False

        def create(**kwargs):
            def enter():
                kwargs['callback'](np.zeros((640, 1), dtype='float32'), 640,
                                   None, SimpleNamespace(input_overflow=False))
                return context
            context.__enter__ = Mock(side_effect=enter)
            return context

        with patch('sounddevice.InputStream', side_effect=create), \
             patch('robot.device_format', return_value=(16000, 1)):
            self.assertEqual(gate.wait(0), 'Naruto')
        gate.kws.reset_stream.assert_called_once()

    def test_fixed_wav_uses_its_sample_rate(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'ikuzo.wav'
            with wave.open(str(path), 'wb') as audio:
                audio.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
                audio.writeframes(np.zeros(2400, dtype='<i2').tobytes())
            samples, rate = load_acknowledgement(path)
            self.assertEqual(rate, 24000)
            self.assertEqual(len(samples), 2400)

    def test_end_returns_to_wake_and_acknowledgement_is_played_once(self):
        from robot import serve_conversations
        args = SimpleNamespace(auto_listen=True, ready_file=None, language='zh',
                               prompt_mode='original', first_clause_chars=16,
                               input_device=0, output_device=3, threshold=.005,
                               silence=.55, metrics=None, wake_model=Path('model'),
                               wake_ack=Path('ikuzo.wav'))
        wake = Mock()
        wake.wait.side_effect = ['Naruto', KeyboardInterrupt]
        with patch('wake_word.NarutoWake', return_value=wake), \
             patch('wake_word.load_acknowledgement', return_value=(np.ones(32), 24000)), \
             patch('robot.play_audio') as play, patch('robot.notify_ready'), \
             patch('robot.listen', return_value=(np.zeros(160), 1)), \
             patch('robot.run_turn', return_value='end'):
            with self.assertRaises(KeyboardInterrupt):
                serve_conversations(args, Mock(), Mock(), None)
            self.assertEqual(wake.wait.call_count, 2)
            self.assertEqual(play.call_count, 2)  # startup chime and fixed ikuzo
            self.assertEqual(play.call_args.args[1], 24000)

    def test_invalid_recognition_does_not_keep_conversation_awake(self):
        from robot import serve_conversations
        args = SimpleNamespace(auto_listen=True, ready_file=None, language='zh',
                               prompt_mode='original', first_clause_chars=16,
                               input_device=0, output_device=3, threshold=.005,
                               silence=.55, metrics=None, wake_model=Path('model'),
                               wake_ack=Path('ikuzo.wav'))
        wake = Mock()
        wake.wait.side_effect = ['Naruto', KeyboardInterrupt]
        now = [0.0]
        def listen(*args, **kwargs):
            now[0] += min(6, kwargs['idle_seconds'])
            return np.zeros(160), now[0]
        with patch('wake_word.NarutoWake', return_value=wake), \
             patch('wake_word.load_acknowledgement', return_value=(np.ones(32), 24000)), \
             patch('robot.play_audio'), patch('robot.notify_ready'), \
             patch('robot.time.perf_counter', side_effect=lambda: now[0]), \
             patch('robot.listen', side_effect=listen) as capture, \
             patch('robot.run_turn', return_value='empty'):
            with self.assertRaises(KeyboardInterrupt):
                serve_conversations(args, Mock(), Mock(), None)
        self.assertEqual(capture.call_count, 3)
        self.assertEqual(now[0], 15)
        self.assertEqual(wake.wait.call_count, 2)

    def test_farewell_plays_once_after_end_then_returns_to_standby(self):
        from robot import serve_conversations
        args = SimpleNamespace(auto_listen=True, ready_file=None, language='zh',
                               prompt_mode='original', first_clause_chars=16,
                               input_device=0, output_device=3, threshold=.005,
                               silence=.55, metrics=None, wake_model=Path('model'),
                               wake_ack=Path('ikuzo.wav'), sleep_ack=Path('matana.wav'))
        wake = Mock()
        wake.wait.side_effect = ['Naruto', KeyboardInterrupt]
        with patch('wake_word.NarutoWake', return_value=wake), \
             patch('wake_word.load_acknowledgement', side_effect=[
                 (np.ones(32), 24000), (np.ones(48), 44100)]), \
             patch('robot.play_audio') as play, patch('robot.notify_ready'), \
             patch('robot.listen', return_value=(np.zeros(160), 1)), \
             patch('robot.run_turn', return_value='end'):
            with self.assertRaises(KeyboardInterrupt):
                serve_conversations(args, Mock(), Mock(), None)
        self.assertEqual(play.call_count, 3)  # startup, wake reply, farewell
        self.assertEqual(play.call_args.args[1], 44100)
        self.assertEqual(wake.wait.call_count, 2)

    def test_farewell_plays_after_idle_but_not_when_stopped_while_waiting(self):
        from robot import serve_conversations
        args = SimpleNamespace(auto_listen=True, ready_file=None, language='zh',
                               prompt_mode='original', first_clause_chars=16,
                               input_device=0, output_device=3, threshold=.005,
                               silence=.55, metrics=None, wake_model=Path('model'),
                               wake_ack=Path('ikuzo.wav'), sleep_ack=Path('farewell.wav'))
        for wake_results, expected_plays in [(['Naruto', KeyboardInterrupt], 3),
                                              ([KeyboardInterrupt], 1)]:
            with self.subTest(wake_results=wake_results):
                wake = Mock()
                wake.wait.side_effect = wake_results
                with patch('wake_word.NarutoWake', return_value=wake), \
                     patch('wake_word.load_acknowledgement', return_value=(np.ones(32), 24000)), \
                     patch('robot.play_audio') as play, patch('robot.notify_ready'), \
                     patch('robot.listen', return_value=(None, None)), \
                     patch('robot.run_turn') as turn:
                    with self.assertRaises(KeyboardInterrupt):
                        serve_conversations(args, Mock(), Mock(), None)
                self.assertEqual(play.call_count, expected_plays)
                turn.assert_not_called()
