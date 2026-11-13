"""Measure digital microphone RMS, using the production audio format."""
import argparse
import json
import time


def main():
    import numpy as np
    import sounddevice as sd
    from robot import device_format

    parser = argparse.ArgumentParser()
    parser.add_argument('--input-device', type=int, required=True)
    parser.add_argument('--seconds', type=float, default=10)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 60:
        parser.error('seconds must be 1-60')
    rate, channels = device_format(args.input_device, 'input', 16000)
    levels = []
    with sd.InputStream(samplerate=rate, channels=channels, dtype='float32',
                        blocksize=round(rate * .02), device=args.input_device) as stream:
        start = time.monotonic()
        while time.monotonic() - start < args.seconds:
            audio, overflow = stream.read(round(rate * .02))
            if overflow:
                raise RuntimeError('input overflow; repeat calibration')
            levels.append(20 * np.log10(max(float(np.sqrt(np.mean(audio ** 2))), 1e-8)))
    print(json.dumps({'unit': 'dBFS RMS, not dB SPL', 'blocks': len(levels),
                      'p10': float(np.percentile(levels, 10)),
                      'p50': float(np.percentile(levels, 50)),
                      'p95': float(np.percentile(levels, 95)),
                      'max': max(levels)}, indent=2))


if __name__ == '__main__':
    main()
