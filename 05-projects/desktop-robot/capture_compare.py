"""Compare saved WAVs through the production gate; never open a microphone."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import time
import wave

import numpy as np

from audio_capture import UtteranceGate
from robot import ASR, RATE, resample_audio
from wake_word import is_naruto


def read_pcm(path):
    with wave.open(str(path), "rb") as audio:
        if audio.getsampwidth() != 2:
            raise ValueError(f"{path}: requires 16-bit PCM WAV")
        samples = np.frombuffer(audio.readframes(audio.getnframes()), "<i2")
        mono = samples.reshape(-1, audio.getnchannels()).mean(axis=1)
        return resample_audio(mono.astype("float32") / 32768, audio.getframerate(), RATE)


def recognizer(assets, language):
    import sherpa_onnx
    folder = assets / ASR
    model = sherpa_onnx.OfflineRecognizer.from_sense_voice(
        model=str(folder / "model.int8.onnx"), tokens=str(folder / "tokens.txt"),
        language=language, use_itn=True, num_threads=2,
    )

    def decode(samples):
        started = time.perf_counter()
        stream = model.create_stream()
        stream.accept_waveform(RATE, samples)
        model.decode_stream(stream)
        return {"text": stream.result.text.strip(), "decode_s": time.perf_counter() - started}
    return decode


def compare(samples, mode, onset_ms, preroll_ms, threshold, decode=None):
    silence = .56 if mode == "wake" else .55
    gate = UtteranceGate(threshold, min_voice_ms=onset_ms, preroll_ms=preroll_ms,
                         silence_seconds=silence, idle_seconds=1e12 if mode == "wake" else 15,
                         max_seconds=3 if mode == "wake" else 12,
                         reject_long=mode == "wake")
    block_size = 640 if mode == "wake" else 320
    padded = np.pad(samples, (0, RATE))
    events = []
    for offset in range(0, len(padded), block_size):
        block = padded[offset:offset + block_size]
        if len(block) < block_size:
            block = np.pad(block, (0, block_size - len(block)))
        result = gate.feed(block)
        if result is None or result.state == "idle":
            continue
        event = {"state": result.state, "decision_s": (offset + block_size) / RATE,
                 "start_s": result.start_sample / RATE if result.start_sample is not None else None,
                 "end_s": result.end_sample / RATE if result.end_sample is not None else None,
                 "first_voice_s": result.first_voice_sample / RATE if result.first_voice_sample is not None else None,
                 "last_voice_s": result.last_voice_sample / RATE if result.last_voice_sample is not None else None}
        if result.state == "done":
            event["duration_s"] = len(result.samples) / RATE
            if decode is not None:
                event.update(decode(result.samples))
                if mode == "wake":
                    event["accepted"] = is_naruto(event["text"])
        events.append(event)
    return {"onset_ms": onset_ms, "preroll_ms": preroll_ms, "events": events}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav", type=Path, nargs="+")
    parser.add_argument("--mode", choices=("chat", "wake"), required=True)
    parser.add_argument("--assets", type=Path, default=Path(".local"))
    parser.add_argument("--language", choices=("zh", "en"), default="zh")
    parser.add_argument("--recognize", action="store_true", help="Run existing local ASR, no LLM/TTS")
    parser.add_argument("--threshold-dbfs", type=float, default=-46)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not np.isfinite(args.threshold_dbfs) or not -96 <= args.threshold_dbfs <= 0:
        parser.error("threshold-dbfs must be -96..0")
    if args.output.exists():
        parser.error("Choose a new output path; previous evidence is preserved")
    paths = [path.resolve(strict=True) for path in args.wav]
    decode = recognizer(args.assets, "ja" if args.mode == "wake" else args.language) if args.recognize else None
    presets = ([(120, 200), (120, 400), (120, 500)] if args.mode == "wake" else
               [(200, 200), (200, 400), (200, 500), (120, 500), (80, 500)])
    report = {"mode": args.mode, "language": "ja" if args.mode == "wake" else args.language,
              "host": platform.platform(), "threshold_dbfs": args.threshold_dbfs,
              "note": "Saved-audio comparison only; no labelled accuracy rate or board latency claimed.",
              "files": []}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf8") as output:
        for path in paths:
            samples = read_pcm(path)
            row = {"file": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                   "duration_s": len(samples) / RATE,
                   "comparisons": [compare(samples, args.mode, onset, preroll,
                                            10 ** (args.threshold_dbfs / 20), decode)
                                   for onset, preroll in presets]}
            report["files"].append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
        json.dump(report, output, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
