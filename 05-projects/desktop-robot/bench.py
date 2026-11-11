"""Run the three dialogue groups with synthetic audio on the real local models."""

import argparse
import os
import time
from pathlib import Path

from robot import Dialogue, RATE, ROOT, Speech, local_server, resample_audio, run_turn, PROMPTS, COMPACT_PROMPTS
from acceleration import warmup_pipeline, cached_input


QUESTIONS = (
    (
        "我给桌面机器人取名叫小蓝。你觉得这个名字怎么样？",
        "它叫什么名字？",
        "给它设计一句简短的自我介绍。",
        "换个话题，给我一个整理桌面的办法。",
        "如果桌上空间很小，应该先收什么？",
    ),
    (
        "我的桌上有一本书和一盆绿萝。应该怎么摆？",
        "刚才我说的植物是什么？",
        "那盆植物适合放在有散射光的位置吗？",
        "换个话题，为什么雨后有时候能看见彩虹？",
        "小学生也能听懂的话应该怎么说？",
    ),
    (
        "我今天用蓝色材料打印了一个圆形外壳。",
        "我刚才说的外壳是什么颜色？",
        "它是什么形状？",
        "换个话题，给我推荐一种简单的休息方式。",
        "如果我只有五分钟，这个办法怎么做？",
    ),
)
ENGLISH_QUESTIONS = (
    (
        "I named my desktop robot Willow. What do you think of the name?",
        "What did I name the robot?",
        "Write a short introduction Willow can say.",
        "Let's change topics. How can I organize a crowded desk?",
        "What should I put away first if I have very little room?",
    ),
    (
        "I have a book and a spider plant on my desk. Where should I put them?",
        "Which plant did I say I have?",
        "Would that plant do well in indirect light?",
        "New topic. Why do we sometimes see rainbows after it rains?",
        "Can you explain that to a child?",
    ),
    (
        "I printed a blue circular case for my robot. What do you think?",
        "What color was the case?",
        "What shape was it?",
        "New topic. What's a simple way to take a break?",
        "How can I try that if I only have five minutes?",
    ),
)


def main():
    import numpy as np

    parser = argparse.ArgumentParser(description="运行离线语音合成输入基准")
    parser.add_argument("--language", choices=("zh", "en"), default="zh")
    parser.add_argument("--threads", type=int, default=4, help="模型推理线程数")
    parser.add_argument("--tts-threads", type=int, help="语音合成线程数，默认与 --threads 相同")
    parser.add_argument("--voice", help="本次音色，优先于 voices.json")
    parser.add_argument("--server", type=Path, help="llama-server 可执行文件或包装脚本")
    parser.add_argument("--gap", type=float, default=0.0, help="每轮之间额外等待的秒数，模拟真人对话间隔")
    parser.add_argument("--speed", type=float)
    parser.add_argument("--batch-threads", type=int)
    parser.add_argument("--cpu-range")
    parser.add_argument("--batch-cpu-range")
    parser.add_argument("--model", type=Path)
    parser.add_argument("--prompt-mode", choices=("original", "compact"), default="original")
    parser.add_argument("--first-clause-chars", type=int, choices=(0,16), default=16)
    parser.add_argument("--metrics", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--no-warmup", action="store_true")
    parser.add_argument("--input-cache", type=Path, help="保存并复用完全相同的16kHz PCM输入，供模型/音色公平对照")
    args = parser.parse_args()
    groups = QUESTIONS if args.language == "zh" else ENGLISH_QUESTIONS
    assets = ROOT / ".local"
    speech = Speech(assets, threads=args.threads, language=args.language, voice=args.voice,
                    tts_threads=args.tts_threads, speed=args.speed)
    output = args.output_dir or assets / ("bench" if args.language == "zh" else "bench-en")
    output.mkdir(exist_ok=True)
    binary = "llama-server.exe" if os.name == "nt" else "llama-server"
    executable = args.server.resolve() if args.server else assets / "llama" / binary
    with local_server(executable, assets, 17860, args.threads, args.batch_threads,
                      args.cpu_range, args.batch_cpu_range, args.model) as chat:
        # 预热轮：完整走一遍识别+生成+合成+播放，不打印计时、不计入统计。
        if not args.no_warmup:
            import json
            prompt = (COMPACT_PROMPTS if args.prompt_mode == "compact" else PROMPTS)[args.language]
            print("静默预热 " + json.dumps(warmup_pipeline(speech, chat, args.language, prompt), ensure_ascii=False), flush=True)
        for group, questions in enumerate(groups, 1):
            dialogue = Dialogue(chat.reply, args.language, chat.reply_stream, args.prompt_mode, args.first_clause_chars)
            for turn, question in enumerate(questions, 1):
                print(f"\n第 {group} 组第 {turn} 轮，合成输入  {question}", flush=True)
                def synthesize_input():
                    return np.concatenate([
                        resample_audio(audio.samples, audio.sample_rate, RATE)
                        for audio in speech.synthesize(question)
                    ])
                cached = args.input_cache/f"{args.language}-{group}-{turn}.wav" if args.input_cache else None
                samples = cached_input(cached,synthesize_input)
                result = output / f"group-{group}-turn-{turn}.wav"
                result.unlink(missing_ok=True)
                if run_turn(dialogue, speech, samples, None, output=result, metrics_path=args.metrics) != "chat":
                    raise RuntimeError(f"第 {group} 组第 {turn} 轮未得到对话回复")
                if args.gap:
                    time.sleep(args.gap)


if __name__ == "__main__":
    main()
