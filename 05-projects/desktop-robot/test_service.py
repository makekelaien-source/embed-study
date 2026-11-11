import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock,patch
from types import SimpleNamespace


class ServiceTests(unittest.TestCase):
    def test_punctuation_only_asr_never_calls_the_model_but_short_speech_does(self):
        from robot import Dialogue
        reply=Mock(return_value='好的。')
        dialogue=Dialogue(reply)
        self.assertEqual(dialogue.turn(' 。！？... '),('empty',''))
        reply.assert_not_called()
        self.assertEqual(dialogue.turn('嗯'),('chat','好的。'))
        self.assertEqual(dialogue.turn('哈哈'),('chat','好的。'))
    def test_audio_selection_survives_changed_card_numbers(self):
        from service_runner import resolve_devices
        devices=[{'name':'CD002-AUDIO: USB Audio (hw:0,0)','max_input_channels':0,'max_output_channels':2},
                 {'name':'USB PnP Sound Device: Audio (hw:3,0)','max_input_channels':1,'max_output_channels':0}]
        self.assertEqual(resolve_devices(devices),(1,0,3,0))
        with self.assertRaises(ValueError):resolve_devices(devices+devices)

    def test_ready_is_reported_after_loading_and_saved_without_transcripts(self):
        from service_runner import notify_ready
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'ready.json'
            with patch.dict('os.environ',{'NOTIFY_SOCKET':'/tmp/test-robot-notify'}), \
                 patch('service_runner.socket.AF_UNIX',1,create=True), \
                 patch('service_runner.socket.socket') as create:
                notify_ready(target)
                create.return_value.__enter__.return_value.sendto.assert_called_once()
            self.assertIn('ready',target.read_text())

    def test_headless_mode_handles_idle_and_end_without_reading_stdin_or_rebeeping(self):
        import numpy as np
        from robot import serve_conversations
        args=SimpleNamespace(auto_listen=True,ready_file=None,language='zh',prompt_mode='original',
                             first_clause_chars=16,input_device=0,output_device=3,threshold=.004,
                             silence=.55,metrics=None)
        chat=Mock()
        with patch('builtins.input',side_effect=AssertionError('stdin must not be read')), \
             patch('robot.play_audio') as play,patch('robot.notify_ready') as ready, \
             patch('robot.listen',side_effect=[(None,None),(np.zeros(1600),1),KeyboardInterrupt]), \
             patch('robot.run_turn',return_value='end') as turn:
            with self.assertRaises(KeyboardInterrupt):serve_conversations(args,chat,Mock(),None)
            self.assertEqual(play.call_count,1)
            ready.assert_called_once()
            turn.assert_called_once()
