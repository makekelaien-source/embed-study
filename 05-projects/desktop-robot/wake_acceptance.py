"""Replay labelled WAVs through the real wake frontend; never record the mic."""
import argparse
import json
from pathlib import Path
import time
import wave

import numpy as np
from robot import resample_audio
from wake_word import SenseVoiceWake, WakeUtterances, is_naruto


def replay(wake, path):
    with wave.open(str(path), 'rb') as audio:
        if audio.getsampwidth() != 2:
            raise ValueError('Replay input requires 16-bit PCM WAV')
        samples = np.frombuffer(audio.readframes(audio.getnframes()), '<i2')
        samples = samples.reshape(-1, audio.getnchannels()).mean(axis=1).astype('float32') / 32768
        samples = resample_audio(samples, audio.getframerate(), 16000)
    gate = WakeUtterances(wake.threshold)
    events = []
    padded = np.pad(samples, (0, 16000))
    for offset in range(0, len(padded), 640):
        block = padded[offset:offset + 640]
        if len(block) < 640:
            block = np.pad(block, (0, 640-len(block)))
        candidate = gate.feed(block)
        if candidate is None:
            continue
        start = time.perf_counter()
        text = wake.recognize(candidate)
        events.append(dict(at_s=offset/16000, duration_s=len(candidate)/16000,
                           text=text, accepted=is_naruto(text),
                           decode_s=time.perf_counter()-start))
    return dict(file=str(path), duration_s=len(samples)/16000, events=events,
                hits=sum(event['accepted'] for event in events))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--assets', type=Path, default=Path('.local'))
    parser.add_argument('--positive', type=Path, nargs='+', required=True)
    parser.add_argument('--negative', type=Path, nargs='+', default=[])
    parser.add_argument('--threshold', type=float, default=10**(-46/20))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a new output path to preserve previous evidence')
    wake = SenseVoiceWake(args.assets, args.threshold)
    results = []
    for label, paths in [('positive', args.positive), ('negative', args.negative)]:
        for path in paths:
            row = dict(label=label, **replay(wake, path))
            results.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
            args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf8')


if __name__ == '__main__':
    main()
