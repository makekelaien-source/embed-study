"""Verified Chinese Matcha/Vocos voice, loaded locally with no network access.

Resources: official k2-fsa release, refreshed 2026-11-12. Baker dataset is
non-commercial; see the model README. This adapter is not a bilingual TTS.
"""
from pathlib import Path
import hashlib
import math
import re

MODEL_DIRECTORY = "matcha-icefall-zh-baker"
VOCODER_FILENAME = "vocos-22khz-univ.onnx"
# Acoustic/front-end hashes derive from the verified official archive SHA256:
# ae70096b19c6e283ea351a26b8a718ce6427c8bde8c1da22eb46a5478d39a69b
# Vocoder hash is also published by k2-fsa/sherpa-onnx-models on Hugging Face.
RESOURCE_HASHES = {
    "model-steps-3.onnx": "47e82b11454edeeb65adc4e44a24fd54c6715cd4d875cc2a20f75545ecc32d4d",
    "tokens.txt": "56209b2bf609d5ac1d66ede6dae7bf5254bd3f8aa24c4a6823713d5b884d87ba",
    "lexicon.txt": "38b886d46aefa50da6322a64d72fd595d5f4fae1051adb160d647541b1e0a4a2",
    "phone.fst": "1ac2b6fa56b1442320c4de7db08353bab8963a2b57f365eebcdd3a2d3562f8d7",
    "date.fst": "eb8aa079ae3cb81d8f4404992f39d61a0cb990947512b5b8d1e54d1f6980e718",
    "number.fst": "743f402181fcfebf76cc2f0546b71fa26476e626fbe4e460fb7b4c3a7a8bd5bd",
    VOCODER_FILENAME: "0574a135aa1db2de6e181050db2ec528496cacd4a4701fc5d7faf9f9804c0081",
}


def verified_resources(assets):
    """Fail closed before invoking ONNX if any resource is missing or modified."""
    assets = Path(assets)
    paths = {}
    for name, expected in RESOURCE_HASHES.items():
        path = assets / name if name == VOCODER_FILENAME else assets / MODEL_DIRECTORY / name
        if not path.is_file():
            raise FileNotFoundError(path)
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            raise ValueError(f"Matcha resource SHA256 mismatch: {path}")
        paths[name] = path
    return paths


class MatchaVoice:
    """Same synthesize(text) iterator contract as robot.Voice.

    A yielded item contains samples and sample_rate. Each sentence is fully
    synthesized before yielding; this must not be advertised as sentence-internal
    streaming. All generation remains on CPU and uses preinstalled sherpa-onnx.
    """
    language = "zh"
    speaker_id = 0

    def __init__(self, assets, threads=2, speed=1.0, *, backend=None):
        if isinstance(threads, bool) or not isinstance(threads, int) or not 1 <= threads <= 8:
            raise ValueError("Matcha threads must be an integer from 1 to 8")
        if isinstance(speed, bool) or not isinstance(speed, (int, float)) or not math.isfinite(speed) or not 0.5 <= speed <= 2.0:
            raise ValueError("Matcha speed must be finite and between 0.5 and 2.0")
        paths = verified_resources(assets)
        if backend is None:
            import sherpa_onnx as backend
        self.speed = float(speed)
        config = backend.OfflineTtsConfig(
            model=backend.OfflineTtsModelConfig(
                matcha=backend.OfflineTtsMatchaModelConfig(
                    acoustic_model=str(paths["model-steps-3.onnx"]),
                    vocoder=str(paths[VOCODER_FILENAME]),
                    lexicon=str(paths["lexicon.txt"]),
                    tokens=str(paths["tokens.txt"]),
                ),
                num_threads=threads,
                provider="cpu",
                debug=False,
            ),
            max_num_sentences=1,
            rule_fsts=",".join(str(paths[name]) for name in ("phone.fst", "date.fst", "number.fst")),
        )
        if not config.validate():
            raise ValueError("Invalid Matcha/Vocos configuration")
        self.tts = backend.OfflineTts(config)

    def synthesize(self, text):
        if not isinstance(text, str):
            raise TypeError("Matcha text must be a string")
        for sentence in re.split(r"(?<=[。！？；])", text):
            if sentence.strip():
                audio = self.tts.generate(sentence, sid=0, speed=self.speed)
                if audio.sample_rate <= 0 or len(audio.samples) == 0:
                    raise RuntimeError("Matcha produced no usable audio")
                yield audio
