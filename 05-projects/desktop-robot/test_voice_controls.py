import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
from robot import Dialogue, SpokenAudio, run_turn, listen
from voice_controls import VolumeControl, dbfs_threshold, volume_clarification, capability_clarification


class ControlsTests(unittest.TestCase):
    def test_bare_open_close_clarifies_without_guessing_or_model(self):
        cases = [('关闭。', '你是想结束对话，还是静音？'),
                 ('关掉', '你是想结束对话，还是静音？'),
                 ('请关闭一下吧', '你是想结束对话，还是静音？'),
                 ('关机', '你是想结束对话，还是静音？'),
                 ('打开。', '你是想恢复声音，还是开始聊天？'),
                 ('请帮我打开一下', '你是想恢复声音，还是开始聊天？')]
        for text, answer in cases:
            with self.subTest(text=text):
                reply = Mock(side_effect=AssertionError('must not claim an unsupported action'))
                reply_stream = Mock(side_effect=AssertionError('must not call model stream'))
                volume = VolumeControl(percent=80, previous=60)
                dialogue = Dialogue(reply, reply_stream=reply_stream, controls=volume)
                self.assertEqual(dialogue.turn(text), ('clarification', answer))
                self.assertEqual((volume.percent, volume.previous), (80, 60))
                self.assertIsNone(dialogue.last_tool)
                self.assertIsNone(dialogue.first_token_at)
                self.assertEqual(dialogue.history[-1]['content'], answer)
                # Explicitly supported commands still take their original routes.
                self.assertEqual(dialogue.turn('结束对话。'), ('end', ''))
                self.assertEqual(list(dialogue.history), [])
                self.assertEqual(dialogue.turn('静音')[0], 'tool')
                self.assertEqual(volume.percent, 0)
                reply.assert_not_called()
                reply_stream.assert_not_called()
        self.assertEqual(capability_clarification('please turn it off', 'en'),
                         'Do you want to end our chat or mute?')
        self.assertEqual(capability_clarification('open it', 'en'),
                         'Do you want to unmute, or start chatting?')

    def test_open_close_discussion_is_not_a_bare_directive(self):
        for text in ['不要关闭', '别打开', '为什么关闭', '关闭？', '打开吗',
                     '如果关闭会怎样', '请解释“关闭”', '“关闭”', '我刚才说关闭',
                     '关闭是什么意思', '打开与关闭的区别', '关心一下天气',
                     'close it?', 'do not close it', 'if you open it',
                     'please explain close', 'I said close it']:
            with self.subTest(text=text):
                self.assertIsNone(capability_clarification(text, 'zh'))
                volume = VolumeControl(percent=80)
                dialogue = Dialogue(Mock(return_value='这是说明。'), controls=volume)
                self.assertEqual(dialogue.turn(text), ('chat', '这是说明。'))
                self.assertEqual(volume.percent, 80)
                self.assertIsNone(dialogue.last_tool)

    def test_observed_close_request_is_spoken_as_clarification_not_completion(self):
        speech = Mock()
        speech.recognize.return_value = '关闭。'
        speech.tool_audio = {'zh': [SpokenAudio(np.ones(32, dtype='float32'), 16000)]}
        speech.synthesize.return_value = [SpokenAudio(np.full(32, .2, dtype='float32'), 16000)]
        volume = VolumeControl(percent=80)
        dialogue = Dialogue(Mock(side_effect=AssertionError('no model')), controls=volume)
        with tempfile.TemporaryDirectory() as folder, patch('robot.play_audio', side_effect=lambda *args: time.perf_counter()):
            target = Path(folder) / 'metrics.jsonl'
            self.assertEqual(run_turn(dialogue, speech, np.zeros(100), None, metrics_path=target),
                             'clarification')
            speech.synthesize.assert_called_once_with('你是想结束对话，还是静音？')
            row = json.loads(target.read_text(encoding='utf8'))
            self.assertEqual(row['kind'], 'clarification')
            self.assertEqual(row['answer'], '你是想结束对话，还是静音？')
            self.assertIsNone(row['tool'])
            self.assertEqual(row['volume_percent'], 80)
            self.assertEqual(row['llm'], {})

    def test_unmatched_direct_volume_request_clarifies_without_model_or_action(self):
        for text in ['把声把音量调高。', '把音量音量调高', '帮我把音量调到一半',
                     'please turn up your volume']:
            with self.subTest(text=text):
                reply = Mock(side_effect=AssertionError('must not promise a tool action'))
                stream_reply = Mock(side_effect=AssertionError('must not call model stream'))
                volume = VolumeControl(percent=80, previous=60)
                dialogue = Dialogue(reply, reply_stream=stream_reply, controls=volume)
                kind, answer = dialogue.turn(text)
                self.assertEqual(kind, 'clarification')
                self.assertEqual(answer, '没能确认调节指令，请再说一次。')
                self.assertEqual((volume.percent, volume.previous), (80, 60))
                self.assertIsNone(dialogue.last_tool)
                self.assertIsNone(dialogue.first_token_at)
                self.assertEqual(dialogue.last_answer, answer)
                self.assertEqual(list(dialogue.history), [
                    {'role': 'user', 'content': text}, {'role': 'assistant', 'content': answer}])
                reply.assert_not_called()
                stream_reply.assert_not_called()
        valid = VolumeControl(percent=80)
        self.assertEqual(valid.execute('把音量调高。', 'zh')['percent'], 100)

    def test_volume_discussion_and_non_actions_remain_normal_chat(self):
        for text in ['不要把音量调高', '为什么把音量调高', '如果把音量调高会怎样',
                     '请解释“把音量调高”', '我刚才说把音量调高', '把音量调高是什么意思',
                     '把音量调高吗', '声音大小的原理', 'why turn up your volume',
                     "don't turn up your volume", 'if you turn up the volume',
                     '你好，今天的天气怎么样']:
            with self.subTest(text=text):
                self.assertIsNone(volume_clarification(text, 'zh'))
                volume = VolumeControl(percent=80)
                reply = Mock(return_value='这是说明。')
                dialogue = Dialogue(reply, controls=volume)
                self.assertEqual(dialogue.turn(text), ('chat', '这是说明。'))
                self.assertEqual(volume.percent, 80)
                self.assertIsNone(dialogue.last_tool)
                reply.assert_called_once()

    def test_clarification_synthesizes_request_not_cached_success_ack(self):
        speech = Mock()
        speech.recognize.return_value = '把声把音量调高。'
        speech.tool_audio = {'zh': [SpokenAudio(np.ones(32, dtype='float32'), 16000)]}
        speech.synthesize.return_value = [SpokenAudio(np.full(32, .2, dtype='float32'), 16000)]
        volume = VolumeControl(percent=80)
        dialogue = Dialogue(Mock(side_effect=AssertionError('no model')), controls=volume)
        with tempfile.TemporaryDirectory() as folder, patch('robot.play_audio', side_effect=lambda *args: time.perf_counter()) as play:
            target = Path(folder) / 'metrics.jsonl'
            self.assertEqual(run_turn(dialogue, speech, np.zeros(100), None, metrics_path=target),
                             'clarification')
            speech.synthesize.assert_called_once_with('没能确认调节指令，请再说一次。')
            np.testing.assert_array_equal(play.call_args.args[0], np.full(32, .2, dtype='float32'))
            self.assertEqual(play.call_args.args[3], .8)
            row = json.loads(target.read_text(encoding='utf8'))
            self.assertEqual(row['kind'], 'clarification')
            self.assertIsNone(row['tool'])
            self.assertIsNone(row['first_token_s'])
            self.assertEqual(row['volume_percent'], 80)
            self.assertEqual(row['llm'], {})

    def test_tool_bypasses_model_and_keeps_state_across_sessions(self):
        reply = Mock(side_effect=AssertionError('model must not run'))
        volume = VolumeControl()
        d = Dialogue(reply, controls=volume)
        self.assertEqual(d.turn('声音小一点。')[0], 'tool')
        self.assertEqual(volume.percent, 80)
        d = Dialogue(reply, controls=volume)
        d.turn('请小声一点')
        self.assertEqual(volume.percent, 60)
        d.turn('音量调到30%')
        self.assertEqual(volume.percent, 30)
        d.turn('静音')
        self.assertEqual(volume.gain, 0)
        d.turn('取消静音')
        self.assertEqual(volume.percent, 30)
        reply.assert_not_called()

    def test_full_utterance_and_bounds(self):
        volume = VolumeControl()
        for text in ['不要调低音量', '他说声音小一点是什么意思', '音量调到101%',
                     '如何调低音量', '如果太吵了怎么办', 'set volume to -1%']:
            self.assertIsNone(volume.execute(text, 'zh'))
        for _ in range(8):
            volume.execute('turn down the volume', 'en')
        self.assertEqual(volume.percent, 0)
        volume.execute('set volume to 100 percent', 'en')
        volume.execute('turn up the volume', 'en')
        self.assertEqual(volume.percent, 100)

    def test_dbfs_validation(self):
        self.assertAlmostEqual(dbfs_threshold(-40), .01)
        for value in [float('nan'), float('inf'), -81, 1]:
            with self.assertRaises(ValueError):
                dbfs_threshold(value)

    def test_actual_playback_applies_gain(self):
        from robot import play_audio
        with patch('robot.device_format', return_value=(16000, 1)), \
             patch('sounddevice.play') as play, patch('sounddevice.wait'):
            play_audio(np.ones(32, dtype='float32'), 16000, 3, .4)
            np.testing.assert_allclose(play.call_args.args[0], .4)

    def test_tool_changes_played_signal_and_emits_execution_metrics(self):
        speech = Mock()
        speech.recognize.return_value = '声音小一点'
        speech.tool_audio = {'zh': [SpokenAudio(np.ones(32, dtype='float32'), 16000)]}
        dialogue = Dialogue(Mock(side_effect=AssertionError('no model')))
        with tempfile.TemporaryDirectory() as folder, patch('robot.play_audio', side_effect=lambda *args: time.perf_counter()) as play:
            target = Path(folder) / 'metrics.jsonl'
            kind = run_turn(dialogue, speech, np.zeros(100), None, metrics_path=target)
            self.assertEqual(kind, 'tool')
            self.assertEqual(play.call_args.args[3], .8)
            speech.synthesize.assert_not_called()
            row = json.loads(target.read_text(encoding='utf8'))
            self.assertTrue(row['tool']['ok'])
            self.assertEqual(row['volume_percent'], 80)
            self.assertIsNone(row['first_token_s'])

    def test_quiet_audio_rejected_even_when_vad_says_speech(self):
        stream = Mock()
        stream.read.return_value = (np.full((320, 1), .005), False)
        context = Mock()
        context.__enter__ = Mock(return_value=stream)
        context.__exit__ = Mock(return_value=False)
        detector = Mock()
        detector.feed.return_value = True
        with patch('robot.device_format', return_value=(16000, 1)), \
             patch('sounddevice.InputStream', return_value=context), \
             patch('robot.time.perf_counter', side_effect=[0, 1, 16]):
            self.assertEqual(listen(0, dbfs_threshold(-38), detector=detector), (None, None))
        self.assertEqual(detector.feed.call_count, 2)


if __name__ == '__main__':
    unittest.main()
