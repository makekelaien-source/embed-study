"""Replay existing labelled WAVs through production wake confirmation, no mic."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from capture_compare import read_pcm
from wake_word import SenseVoiceWake, WakeUtterances, is_naruto


def board_facts(required=False):
    facts = {}
    for name, zone in (("cpu_c", 0), ("skin_c", 7)):
        path = Path(f"/sys/class/thermal/thermal_zone{zone}/temp")
        if path.exists():
            facts[name] = int(path.read_text()) / 1000
        elif required:
            raise RuntimeError("Missing temperature: " + str(path))
    memory = Path("/proc/meminfo")
    if memory.exists():
        for line in memory.read_text().splitlines():
            if line.startswith("MemAvailable:"):
                facts["mem_available_kib"] = int(line.split()[1])
                break
    if facts.get("cpu_c", 0) >= 70 or facts.get("skin_c", 0) >= 43:
        raise RuntimeError("Temperature limit reached: " + json.dumps(facts))
    if facts.get("mem_available_kib", 1024 * 1024) < 384 * 1024:
        raise RuntimeError("Insufficient available memory: " + json.dumps(facts))
    return facts


def replay(wake, path, label, emit, guarded=False):
    samples = read_pcm(path)
    if len(samples) > 60 * 16000:
        raise ValueError("Diagnostic input must be no longer than 60 seconds")
    gate = WakeUtterances(wake.threshold, wake.min_voice_ms, wake.preroll_ms,
                          wake.silence_seconds)
    emit({"event": "source", "file": str(path), "label": label,
          "duration_s": len(samples) / 16000,
          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    baseline_hits = candidate_hits = count = 0
    padded = np.pad(samples, (0, 16000))
    for offset in range(0, len(padded), 640):
        block = padded[offset:offset + 640]
        if len(block) < 640:
            block = np.pad(block, (0, 640 - len(block)))
        audio = gate.feed(block)
        if audio is None:
            continue
        before = board_facts(guarded)
        started = time.perf_counter()
        text = wake.recognize(audio)
        primary_s = time.perf_counter() - started
        decision = wake.confirm(text, audio, gate.last_result)
        capture = gate.last_result
        baseline_hits += int(is_naruto(text))
        candidate_hits += int(decision["accepted"])
        count += 1
        emit({"event": "segment", "file": str(path), "label": label,
              "start_s": capture.start_sample / 16000,
              "end_s": capture.end_sample / 16000,
              "primary_text": text, "primary_accepted": is_naruto(text),
              "primary_decode_s": primary_s, "confirmation": decision,
              "all_decode_s": time.perf_counter() - started,
              "before": before, "after": board_facts(guarded)})
    summary = {"event": "file_summary", "file": str(path), "label": label,
               "segments": count, "baseline_accepted_segments": baseline_hits,
               "candidate_accepted_segments": candidate_hits,
               "note": "Segments are not independent human attempts; no recall rate computed."}
    emit(summary)
    return label == "negative" and candidate_hits > 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, default=Path(".local"))
    parser.add_argument("--positive", type=Path, nargs="+", default=[])
    parser.add_argument("--negative", type=Path, nargs="+", default=[])
    parser.add_argument("--board-guard", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.positive and not args.negative:
        parser.error("Supply existing positive or negative WAVs")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf8") as stream:
        def emit(row):
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush()
            if row["event"] == "file_summary":
                print(json.dumps(row, ensure_ascii=False), flush=True)
        emit({"event": "before_load", **board_facts(args.board_guard)})
        wake = SenseVoiceWake(args.assets, 10 ** (-46 / 20), confirmation="auto-consensus")
        if wake.confirmation_recognizer is None:
            raise RuntimeError("Candidate unavailable: " + str(wake.confirmation_error))
        emit({"event": "after_load", **board_facts(args.board_guard)})
        rejected = False
        for label, paths in (("positive", args.positive), ("negative", args.negative)):
            for path in paths:
                rejected |= replay(wake, path.resolve(strict=True), label, emit, args.board_guard)
        emit({"event": "complete", "negative_false_accept": rejected,
              "scope": "Saved-audio lab comparison only; no microphone or acoustic latency."})
        return 3 if rejected else 0


if __name__ == "__main__":
    raise SystemExit(main())
