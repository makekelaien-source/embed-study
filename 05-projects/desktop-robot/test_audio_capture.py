import unittest
from unittest.mock import Mock, patch

import numpy as np

from audio_capture import UtteranceGate


RATE = 16000


def frame(level, ms=20):
    return np.full(RATE * ms // 1000, level, dtype='float32')


def events(gate, frames):
    found = []
    for audio in frames:
        result = gate.feed(audio)
        if result is not None:
            found.append(result)
    return found


class SegmentationTests(unittest.TestCase):
    def test_larger_preroll_preserves_a_weak_first_sound(self):
        source = [frame(0)] * 10 + [frame(.002)] * 5 + [frame(.02)] * 10 + [frame(0)] * 30
        old = events(UtteranceGate(.005, 200, 200), source)[0]
        enlarged = events(UtteranceGate(.005, 200, 500), source)[0]
        self.assertEqual(old.state, 'done')
        self.assertFalse(np.any(old.samples == np.float32(.002)))
        self.assertEqual(np.count_nonzero(enlarged.samples == np.float32(.002)), 5 * 320)
        self.assertEqual(old.first_voice_sample, enlarged.first_voice_sample)
        self.assertEqual(old.end_sample, enlarged.end_sample)  # history adds no waiting
        full = np.concatenate(source)
        np.testing.assert_array_equal(enlarged.samples,
                                      full[enlarged.start_sample:enlarged.end_sample])

    def test_interrupted_onset_does_not_accumulate_loud_frames(self):
        source = ([frame(.02)] * 3 + [frame(0)]) * 5 + [frame(0)] * 30
        self.assertEqual(events(UtteranceGate(.005, 80, 500), source), [])

    def test_single_loud_impulse_never_starts_an_utterance(self):
        source = [frame(0)] * 20 + [frame(.8)] + [frame(0)] * 50
        self.assertEqual(events(UtteranceGate(.005, 80, 500), source), [])

    def test_tail_wait_keeps_short_pause_and_last_word(self):
        gate = UtteranceGate(.005, 80, 400, silence_seconds=.55)
        first = [frame(.02)] * 6
        pause = [frame(0)] * 20  # 400ms is a sentence-internal pause
        last = [frame(.03)] * 5
        self.assertEqual(events(gate, first + pause + last + [frame(0)] * 27), [])
        result = gate.feed(frame(0))
        self.assertEqual(result.state, 'done')
        self.assertEqual(np.count_nonzero(result.samples == np.float32(.03)), 5 * 320)
        self.assertEqual(result.end_sample - result.last_voice_sample, 28 * 320)

    def test_idle_deadline_cannot_be_reopened_by_late_voice(self):
        gate = UtteranceGate(.005, 80, 200, idle_seconds=1)
        self.assertEqual(events(gate, [frame(0)] * 49), [])
        result = gate.feed(frame(.02))
        self.assertEqual(result.state, 'idle')
        self.assertIsNone(result.samples)

    def test_detector_is_combined_with_rms_floor(self):
        for signal, vad in [(.02, False), (.002, True)]:
            gate = UtteranceGate(.005, 80, 200)
            self.assertTrue(all(gate.feed(frame(signal), speech_detected=vad) is None
                                for _ in range(50)))

    def test_live_elapsed_sets_endpoint_and_speech_end(self):
        gate = UtteranceGate(.005, 80, 200, silence_seconds=.55)
        for now in (1.00, 1.02, 1.04, 1.06):
            self.assertIsNone(gate.feed(frame(.02), elapsed=now))
        self.assertIsNone(gate.feed(frame(0), elapsed=1.60))
        result = gate.feed(frame(0), elapsed=1.62)
        self.assertEqual(result.state, 'done')
        self.assertEqual(result.last_voice_s, 1.06)
        self.assertEqual(result.first_voice_s, 1.06)

    def test_live_chat_uses_configured_history_and_original_speech_end(self):
        from robot import listen
        source = [frame(0)] * 10 + [frame(.002)] * 5 + [frame(.02)] * 10 + [frame(0)] * 28
        stream = Mock()
        stream.read.side_effect = [(audio[:, None], False) for audio in source]
        context = Mock()
        context.__enter__ = Mock(return_value=stream)
        context.__exit__ = Mock(return_value=False)
        with patch('robot.device_format', return_value=(16000, 1)), \
             patch('sounddevice.InputStream', return_value=context), \
             patch('robot.time.perf_counter', side_effect=[0] + [i * .02 for i in range(1, 54)]):
            samples, speech_end = listen(0, .005, .55, min_voice_ms=200, preroll_ms=500)
        np.testing.assert_array_equal(samples, np.concatenate(source))
        self.assertEqual(speech_end, .5)

    def test_native_stereo_listen_preserves_original_channel_energy_gate(self):
        from robot import listen, resample_audio
        quiet = np.zeros((960, 2), dtype='float32')
        one_channel = quiet.copy()
        one_channel[:, 0] = .008
        self.assertGreater(float(np.sqrt(np.mean(one_channel ** 2))), .005)
        self.assertLess(float(np.sqrt(np.mean(one_channel.mean(axis=1) ** 2))), .005)
        source = [quiet] * 10 + [one_channel] * 6 + [quiet] * 28
        stream = Mock()
        stream.read.side_effect = [(audio, False) for audio in source]
        context = Mock()
        context.__enter__ = Mock(return_value=stream)
        context.__exit__ = Mock(return_value=False)
        with patch('robot.device_format', return_value=(48000, 2)), \
             patch('sounddevice.InputStream', return_value=context), \
             patch('robot.time.perf_counter', side_effect=[0] + [i * .02 for i in range(1, 45)]):
            samples, speech_end = listen(0, .005, .55, min_voice_ms=120, preroll_ms=200)
        # Confirmation at320ms retains the preceding200ms; the source's first
        # 120ms is outside that history. Mono output remains the original mix.
        expected = resample_audio(np.concatenate(source)[5760:].mean(axis=1), 48000, 16000)
        np.testing.assert_array_equal(samples, expected)
        self.assertGreater(float(np.max(samples)), .003)
        self.assertEqual(speech_end, .32)

    def test_wake_duration_is_independent_of_extra_preroll(self):
        for history in (200, 500):
            gate = UtteranceGate(.005, 120, history, silence_seconds=.56,
                                 idle_seconds=1e12, max_seconds=3, reject_long=True)
            # Five quiet blocks + onset confirmation; then 2.96 sec still allowed.
            self.assertEqual(events(gate, [frame(0, 40)] * 5 + [frame(.02, 40)] * 3), [])
            self.assertEqual(events(gate, [frame(.02, 40)] * 74), [])
            result = gate.feed(frame(.02, 40))
            self.assertEqual(result.state, 'blocked')
            self.assertTrue(gate.blocked)
            self.assertEqual(events(gate, [frame(.02, 40)] * 20 + [frame(0, 40)] * 13), [])
            self.assertTrue(gate.blocked)
            self.assertIsNone(gate.feed(frame(0, 40)))
            self.assertFalse(gate.blocked)
            recovered = events(gate, [frame(.02, 40)] * 5 + [frame(0, 40)] * 14)
            self.assertEqual([row.state for row in recovered], ['done'])

    def test_native_rate_and_partial_preroll_preserve_exact_sample_bounds(self):
        gate = UtteranceGate(.005, 80, 125, sample_rate=48000)
        source = np.arange(960 * 50, dtype='float32') / 1e6
        source[:960 * 10] = 0
        source[960 * 20:] = 0
        found = []
        for offset in range(0, len(source), 960):
            result = gate.feed(source[offset:offset + 960])
            if result is not None:
                found.append(result)
        self.assertEqual(len(found), 1)
        result = found[0]
        self.assertEqual(len(result.samples), result.end_sample - result.start_sample)
        np.testing.assert_array_equal(result.samples, source[result.start_sample:result.end_sample])

    def test_invalid_parameters_and_pcm_fail_before_capture(self):
        for kwargs in [dict(threshold=float('nan')), dict(threshold=0),
                       dict(min_voice_ms=0), dict(min_voice_ms=float('inf')),
                       dict(preroll_ms=0), dict(preroll_ms=2001),
                       dict(silence_seconds=.1), dict(silence_seconds=float('nan')),
                       dict(idle_seconds=0), dict(max_seconds=0), dict(sample_rate=0)]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                UtteranceGate(**(dict(threshold=.005) | kwargs))
        gate = UtteranceGate(.005)
        for bad in ([], [[0]], [float('nan')], [float('inf')]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                gate.feed(bad)
        for level in (-.1, float('nan'), float('inf')):
            with self.subTest(level=level), self.assertRaises(ValueError):
                gate.feed(frame(0), level=level)
        gate.feed(frame(0), elapsed=1)
        with self.assertRaises(ValueError):
            gate.feed(frame(0), elapsed=.5)


if __name__ == '__main__':
    unittest.main()
