"""Isolated bilingual streaming Zipformer screen; not the production recognizer.

No transcript rewriting. Hotwords act only inside acoustic decoding. The caller
must decide whether the candidate passes accuracy and target-device timing gates.
"""
from pathlib import Path
import hashlib
import json
import math

MODEL_FILES = {
    'encoder': 'encoder-epoch-99-avg-1.int8.onnx',
    'decoder': 'decoder-epoch-99-avg-1.onnx',
    'joiner': 'joiner-epoch-99-avg-1.int8.onnx',
    'tokens': 'tokens.txt',
    'bpe_vocab': 'bpe.vocab',
}
MODEL_PINS = {
    'encoder': 'db6f51551762e40e549166fe041ea3e45464370b595e9ad23f06478ec3794fbb',
    'decoder': '89be509a83175261695bdef5fd1c7b9ab1129a663d1284e7ba9f8507b21e0906',
    'joiner': 'bdda356d6f9b8c2d7cee9ee0e26075fa537490f7fd06520be408d287073667b9',
}


def verify_assets(assets):
    root = Path(assets)
    manifest = json.loads((root / 'provenance.json').read_text(encoding='utf-8-sig'))
    if manifest.get('repo') != 'csukuangfj/k2fsa-zipformer-bilingual-zh-en-t':
        raise ValueError('Wrong ASR model provenance')
    records = {item['name']: item for item in manifest['files']}
    paths = {}
    for key, name in MODEL_FILES.items():
        path = root / name
        if not path.is_file():
            raise FileNotFoundError(path)
        with path.open('rb') as source:
            digest = hashlib.file_digest(source, 'sha256').hexdigest()
        record = records.get(name)
        if not record or path.stat().st_size != record['size'] or digest != record['sha256']:
            raise ValueError(f'ASR artifact integrity mismatch: {name}')
        if key in MODEL_PINS and digest != MODEL_PINS[key]:
            raise ValueError(f'Wrong pinned ASR model: {name}')
        paths[key] = str(path)
    return paths


class AsrCandidate:
    def __init__(self, assets, threads=2, hotwords_file=None, hotwords_score=1.5, *, backend=None):
        if isinstance(threads, bool) or not isinstance(threads, int) or not 1 <= threads <= 8:
            raise ValueError('threads must be 1..8')
        if not isinstance(hotwords_score, (int, float)) or not math.isfinite(hotwords_score) or hotwords_score < 0:
            raise ValueError('hotwords_score must be finite and nonnegative')
        if hotwords_file is not None and not Path(hotwords_file).is_file():
            raise FileNotFoundError(hotwords_file)
        paths = verify_assets(assets)
        if backend is None:
            import sherpa_onnx as backend
        self.recognizer = backend.OnlineRecognizer.from_transducer(
            **paths, num_threads=threads, sample_rate=16000,
            decoding_method='modified_beam_search', max_active_paths=4,
            modeling_unit='cjkchar+bpe', hotwords_file=str(hotwords_file) if hotwords_file else '',
            hotwords_score=float(hotwords_score), provider='cpu',
            enable_endpoint_detection=False,
        )

    def recognize(self, samples, sample_rate=16000):
        """File replay in streaming chunks; no real-time sleeps or audio playback.

        Zero tail padding flushes the model's right context and is not new speech.
        Offline compute time is not an endpoint-to-audible-response measurement.
        """
        import numpy as np
        if sample_rate != 16000:
            raise ValueError('Replay requires 16kHz input; resample explicitly upstream')
        samples = np.asarray(samples, dtype=np.float32)
        if samples.ndim != 1 or not np.isfinite(samples).all():
            raise ValueError('Input must be finite mono PCM')
        if not len(samples):
            return ''
        stream = self.recognizer.create_stream()
        for offset in range(0, len(samples), 320):
            stream.accept_waveform(sample_rate, samples[offset:offset+320])
            while self.recognizer.is_ready(stream):
                self.recognizer.decode_stream(stream)
        stream.accept_waveform(sample_rate, np.zeros(12800, dtype=np.float32))
        stream.input_finished()
        while self.recognizer.is_ready(stream):
            self.recognizer.decode_stream(stream)
        return self.recognizer.get_result(stream).strip()
