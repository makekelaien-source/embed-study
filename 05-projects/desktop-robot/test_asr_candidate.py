import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch
import numpy as np
from asr_candidate import AsrCandidate


class AsrCandidateTests(unittest.TestCase):
    def setUp(self):
        self.stream = Mock()
        self.recognizer = Mock()
        self.recognizer.create_stream.return_value = self.stream
        self.recognizer.is_ready.return_value = False
        self.recognizer.get_result.return_value = ' I2C test '
        self.factory = Mock(return_value=self.recognizer)
        self.backend = SimpleNamespace(OnlineRecognizer=SimpleNamespace(from_transducer=self.factory))
        p = patch('asr_candidate.verify_assets', return_value=dict(encoder='e', decoder='d', joiner='j', tokens='t', bpe_vocab='b'))
        p.start(); self.addCleanup(p.stop)

    def make(self, **kw): return AsrCandidate('.', backend=self.backend, **kw)

    def test_exact_decoder_contract(self):
        self.make()
        args = self.factory.call_args.kwargs
        self.assertEqual(args['decoding_method'], 'modified_beam_search')
        self.assertEqual(args['modeling_unit'], 'cjkchar+bpe')
        self.assertEqual(args['bpe_vocab'], 'b')
        self.assertEqual(args['hotwords_file'], '')
        self.assertEqual(args['max_active_paths'], 4)
        self.assertFalse(args['enable_endpoint_detection'])

    def test_hotword_option(self):
        with TemporaryDirectory() as d:
            p = Path(d)/'hotwords.txt';p.write_text('STATIC\nUART\n')
            self.make(hotwords_file=p, hotwords_score=1.5)
            self.assertEqual(self.factory.call_args.kwargs['hotwords_file'], str(p))

    def test_no_transcript_replacement(self):
        self.recognizer.get_result.return_value = 'iphone C'
        self.assertEqual(self.make().recognize(np.zeros(640)), 'iphone C')

    def test_stream_is_finalized(self):
        result = self.make().recognize(np.zeros(640))
        self.assertEqual(result, 'I2C test')
        self.assertEqual(self.stream.accept_waveform.call_count, 3)
        self.stream.input_finished.assert_called_once()

    def test_empty(self):
        self.assertEqual(self.make().recognize([]), '')
        self.recognizer.create_stream.assert_not_called()

    def test_sample_rate(self):
        with self.assertRaises(ValueError): self.make().recognize([0.1], 48000)

    def test_bad_pcm(self):
        for samples in ([[0.1]], [float('nan')], [float('inf')]):
            with self.subTest(samples=samples), self.assertRaises(ValueError): self.make().recognize(samples)

    def test_bad_threads(self):
        for n in [0, 9, True, 1.5]:
            with self.subTest(n=n), self.assertRaises(ValueError): self.make(threads=n)

    def test_bad_score(self):
        for n in [-1, float('nan'), float('inf')]:
            with self.subTest(n=n), self.assertRaises(ValueError): self.make(hotwords_score=n)



class AsrAssetIntegrityTests(unittest.TestCase):
    def setUp(self):
        import hashlib, json
        import asr_candidate as m
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.records = []
        self.pins = {}
        for key, name in m.MODEL_FILES.items():
            data = name.encode(); (self.root / name).write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            self.records.append({'name': name, 'size': len(data), 'sha256': digest})
            if key in m.MODEL_PINS: self.pins[key] = digest
        self.manifest = {'repo': 'csukuangfj/k2fsa-zipformer-bilingual-zh-en-t', 'files': self.records}
        self.save()
        p = patch.dict(m.MODEL_PINS, self.pins, clear=True); p.start(); self.addCleanup(p.stop)

    def save(self):
        import json
        (self.root/'provenance.json').write_text(json.dumps(self.manifest), encoding='utf8')

    def test_valid_artifacts(self):
        from asr_candidate import verify_assets, MODEL_FILES
        self.assertEqual(set(verify_assets(self.root)), set(MODEL_FILES))

    def test_missing_artifact(self):
        from asr_candidate import verify_assets
        (self.root/'tokens.txt').unlink()
        with self.assertRaises(FileNotFoundError): verify_assets(self.root)

    def test_changed_frontend(self):
        from asr_candidate import verify_assets
        (self.root/'bpe.vocab').write_text('different')
        with self.assertRaisesRegex(ValueError, 'integrity'): verify_assets(self.root)

    def test_changed_model_pin(self):
        import hashlib
        from asr_candidate import verify_assets
        name = 'encoder-epoch-99-avg-1.int8.onnx'; data = b'wrong model'
        (self.root/name).write_bytes(data)
        for r in self.records:
            if r['name'] == name:r.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
        self.save()
        with self.assertRaisesRegex(ValueError, 'pinned'): verify_assets(self.root)

    def test_wrong_publisher(self):
        from asr_candidate import verify_assets
        self.manifest['repo'] = 'someone/else';self.save()
        with self.assertRaisesRegex(ValueError, 'provenance'): verify_assets(self.root)

if __name__ == '__main__': unittest.main()
