"""Model-free adapter contract and fail-closed resource tests."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import matcha_voice as m


class MatchaVoiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / m.MODEL_DIRECTORY).mkdir()
        self.pins = {}
        for name in m.RESOURCE_HASHES:
            path = self.root / name if name == m.VOCODER_FILENAME else self.root / m.MODEL_DIRECTORY / name
            data = name.encode()
            path.write_bytes(data)
            self.pins[name] = hashlib.sha256(data).hexdigest()
        self.pin_patch = patch.dict(m.RESOURCE_HASHES, self.pins, clear=True)
        self.pin_patch.start()
        self.addCleanup(self.pin_patch.stop)
        self.audio = SimpleNamespace(samples=[0.1, -0.1], sample_rate=22050)
        self.engine = Mock()
        self.engine.generate.return_value = self.audio
        self.config = Mock()
        self.config.validate.return_value = True
        self.backend = SimpleNamespace(
            OfflineTtsMatchaModelConfig=Mock(side_effect=lambda **kw: kw),
            OfflineTtsModelConfig=Mock(side_effect=lambda **kw: kw),
            OfflineTtsConfig=Mock(return_value=self.config),
            OfflineTts=Mock(return_value=self.engine),
        )

    def voice(self, **kw):
        return m.MatchaVoice(self.root, backend=self.backend, **kw)

    def test_config_uses_pinned_local_resources(self):
        self.voice(threads=4)
        model = self.backend.OfflineTtsModelConfig.call_args.kwargs
        self.assertEqual(model['provider'], 'cpu')
        self.assertEqual(model['num_threads'], 4)
        self.assertNotIn('dict_dir', model['matcha'])
        cfg = self.backend.OfflineTtsConfig.call_args.kwargs
        self.assertEqual(cfg['max_num_sentences'], 1)
        self.assertEqual(len(cfg['rule_fsts'].split(',')), 3)

    def test_sentence_audio_contract_and_speed(self):
        voice = self.voice(speed=0.9)
        self.assertEqual(list(voice.synthesize('你好。现在可以开始！')), [self.audio, self.audio])
        self.assertEqual(self.engine.generate.call_args_list[0].args, ('你好。',))
        self.assertEqual(self.engine.generate.call_args_list[0].kwargs, {'sid': 0, 'speed': 0.9})

    def test_empty_text_does_not_generate(self):
        self.assertEqual(list(self.voice().synthesize('  ')), [])
        self.engine.generate.assert_not_called()

    def test_wrong_type_rejected(self):
        with self.assertRaises(TypeError):
            list(self.voice().synthesize(None))

    def test_missing_resource_stops_before_backend(self):
        (self.root / m.VOCODER_FILENAME).unlink()
        with self.assertRaises(FileNotFoundError): self.voice()
        self.backend.OfflineTts.assert_not_called()

    def test_tampered_resource_stops_before_backend(self):
        (self.root / m.MODEL_DIRECTORY / 'tokens.txt').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'SHA256'): self.voice()
        self.backend.OfflineTts.assert_not_called()

    def test_invalid_config_stops_before_model(self):
        self.config.validate.return_value = False
        with self.assertRaisesRegex(ValueError, 'configuration'): self.voice()
        self.backend.OfflineTts.assert_not_called()

    def test_invalid_speed(self):
        for speed in [float('nan'), float('inf'), 0, 2.1, True, '1']:
            with self.subTest(speed=speed), self.assertRaises(ValueError): self.voice(speed=speed)

    def test_invalid_threads(self):
        for threads in [0, 9, 1.5, True, '2']:
            with self.subTest(threads=threads), self.assertRaises(ValueError): self.voice(threads=threads)

    def test_empty_audio_fails(self):
        self.engine.generate.return_value = SimpleNamespace(samples=[], sample_rate=22050)
        with self.assertRaisesRegex(RuntimeError, 'usable audio'): list(self.voice().synthesize('你好。'))

    def test_invalid_sample_rate_fails(self):
        self.engine.generate.return_value = SimpleNamespace(samples=[0.1], sample_rate=0)
        with self.assertRaisesRegex(RuntimeError, 'usable audio'): list(self.voice().synthesize('你好。'))


if __name__ == '__main__': unittest.main()
