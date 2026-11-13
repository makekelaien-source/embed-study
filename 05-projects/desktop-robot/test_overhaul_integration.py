"""Integration regressions for factual telemetry and fresh per-turn state."""
from datetime import datetime, timezone
from pathlib import Path
import time
import unittest
from unittest.mock import Mock, patch
import numpy as np

from device_status import DeviceStatus
from robot import Dialogue, SpokenAudio, run_turn


class OverhaulIntegrationTests(unittest.TestCase):
    def status(self, temp='48750'):
        def read(path):
            if path.name == 'type':
                return 'cpub_thermal_zone'
            if isinstance(temp, Exception):
                raise temp
            return temp
        return DeviceStatus(root='/fake', read_text=read,
                            list_zones=lambda root: [root / 'thermal_zone1'],
                            clock=lambda: datetime(2026, 11, 13, tzinfo=timezone.utc))

    def test_real_device_status_bypasses_llm(self):
        model = Mock(side_effect=AssertionError('Telemetry must not call the model'))
        dialogue = Dialogue(model)
        dialogue.device_status = self.status()
        kind, result = dialogue.turn('这块香橙派现在的CPU温度多少？')
        self.assertEqual(kind, 'tool')
        self.assertEqual(result['celsius'], 48.75)
        self.assertEqual(dialogue.last_tool, result)
        self.assertTrue(result['ok'])
        model.assert_not_called()

    def test_read_failure_also_bypasses_llm(self):
        model = Mock(side_effect=AssertionError('No invented temperature'))
        dialogue = Dialogue(model)
        dialogue.device_status = self.status(PermissionError('no sensor access'))
        kind, result = dialogue.turn('CPU温度多少')
        self.assertEqual(kind, 'tool')
        self.assertFalse(result['ok'])
        self.assertIn('无法确认', result['answer'])
        model.assert_not_called()

    def test_empty_input_clears_stale_answer_and_tool(self):
        for empty in ('', ' ', '。', '？！'):
            with self.subTest(empty=empty):
                dialogue = Dialogue(lambda messages: 'A previous real answer.')
                dialogue.turn('Explain arrays')
                self.assertTrue(dialogue.last_answer)
                dialogue.last_tool = {'tool': 'old'}
                self.assertEqual(dialogue.turn_stream(empty), ('empty', None))
                self.assertEqual(dialogue.last_answer, '')
                self.assertIsNone(dialogue.last_tool)

    def test_temperature_synthesizes_fresh_text_not_volume_cache(self):
        speech = Mock()
        speech.recognize.return_value = '这块香橙派现在的CPU温度多少？'
        cached = SpokenAudio(np.full(32, -0.8, dtype='float32'), 16000)
        live = SpokenAudio(np.full(32, 0.2, dtype='float32'), 16000)
        speech.tool_audio = {'zh': [cached]}
        speech.synthesize.return_value = [live]
        dialogue = Dialogue(Mock(side_effect=AssertionError('No model')))
        dialogue.device_status = self.status()
        with patch('robot.play_audio', side_effect=lambda *args: time.perf_counter()) as play:
            self.assertEqual(run_turn(dialogue, speech, np.zeros(100), None), 'tool')
        speech.synthesize.assert_called_once_with(dialogue.last_tool['answer'])
        self.assertIn('48.8', speech.synthesize.call_args.args[0])
        np.testing.assert_array_equal(play.call_args.args[0], live.samples)
        self.assertEqual(dialogue.last_answer, dialogue.last_tool['answer'])


if __name__ == '__main__':
    unittest.main()
