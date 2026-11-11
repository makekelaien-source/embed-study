"""Controlled board-side A/B runner; never records the live microphone."""
import argparse
import json
import shutil
import time
import wave
from pathlib import Path

import numpy as np
from robot import (ROOT, RATE, Speech, Dialogue, PROMPTS, COMPACT_PROMPTS,
                   local_server, resample_audio, run_turn, save_wav)
from acceleration import warmup_pipeline, SileroDetector


def load_recording(path):
    with wave.open(str(path), "rb") as f:
        if f.getsampwidth() != 2:
            raise ValueError("录音需要 16 位 PCM")
        a = np.frombuffer(f.readframes(f.getnframes()), "<i2").astype("float32")/32768
        return resample_audio(a.reshape(-1, f.getnchannels()).mean(axis=1), f.getframerate(), RATE)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=ROOT/".local/speed-results")
    p.add_argument("--batch-threads", type=int, default=2)
    p.add_argument("--batch-range", default="6-7")
    p.add_argument("--model", type=Path)
    p.add_argument("--voice", default="theresa")
    p.add_argument("--tts-threads", type=int, default=8)
    p.add_argument("--inputs-dir", type=Path, help="重用已缓存的input-0/1/2.wav，音色对照必须使用同一输入")
    p.add_argument("--cases", default="cold,warm,batch4,batch8,compact,early")
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    assets = ROOT/".local"
    speech = Speech(assets, 2, "zh", args.voice, args.tts_threads, 0.9)
    if args.inputs_dir:
        samples=[load_recording(args.inputs_dir/f"input-{i}.wav") for i in range(3)]
    else:
        samples = [load_recording(assets/"human-mic-check-10s.wav")]
        # Cache identical inputs once; input synthesis is never in the latency metric.
        for question in ["我叫什么名字？", "给我一个整理桌面的建议。"]:
            samples.append(np.concatenate([resample_audio(c.samples,c.sample_rate,RATE)
                                           for c in speech.synthesize(question)]))
    for i, sample in enumerate(samples):
        save_wav(args.output/f"input-{i}.wav", sample, RATE)
    cases = {
        "cold": (2,"6-7",False,"original",0),
        "warm": (2,"6-7",True,"original",0),
        "batch4": (4,"4-7",True,"original",0),
        "batch8": (8,"0-7",True,"original",0),
        "compact": (args.batch_threads,args.batch_range,True,"compact",0),
        "early": (args.batch_threads,args.batch_range,True,"compact",16),
        "early-original": (args.batch_threads,args.batch_range,True,"original",16),
        "model": (args.batch_threads,args.batch_range,True,"original",16),
    }
    executable = assets/"llama/llama-server"
    for name in args.cases.split(","):
        batch,cpus,warm,mode,limit = cases[name]
        target = args.output/name
        target.mkdir()
        with local_server(executable,assets,17860,2,batch,"6-7",cpus,args.model) as chat:
            chat.seed = 42
            print("CASE",name,"batch",batch,"cpu",cpus,flush=True)
            if warm:
                print("WARMUP", json.dumps(warmup_pipeline(speech,chat,"zh",
                    (COMPACT_PROMPTS if mode=="compact" else PROMPTS)["zh"])),flush=True)
            dialogue = Dialogue(chat.reply,"zh",chat.reply_stream,mode,limit)
            for i, sample in enumerate(samples):
                run_turn(dialogue,speech,sample,None,output=target/f"reply-{i}.wav",
                         metrics_path=target/"metrics.jsonl")
                time.sleep(8)
        shutil.copy2(assets/"llama.log",target/"llama.log")
        (target/"config.json").write_text(json.dumps({"batch_threads":batch,
            "batch_range":cpus,"warmup":warm,"prompt_mode":mode,"first_clause_chars":limit,
            "voice":args.voice,"speed":0.9,"tts_threads":args.tts_threads,
            "model":str(args.model or assets/"chat.gguf")}),encoding="utf8")
        time.sleep(10)


if __name__ == "__main__":
    main()
