"""Small, hardware-independent pieces of the offline latency pipeline."""

import math
import re
import time


def tts_model_path(folder):
    for name in ("model.onnx", "theresa.onnx"):
        path=folder/name
        if path.is_file():
            return path
    raise FileNotFoundError(folder/"model.onnx")


def cached_input(path, create):
    from robot import read_wav, save_wav, RATE
    if path is None:
        return create()
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        save_wav(path,create(),RATE)
    return read_wav(path)


def split_first_clause(deltas, enders, limit=16):
    """Bound the first Chinese clause, allowing protected spans to exceed limit.

    A lookahead character prevents cutting a number or an English token whose
    final character happens to arrive at the size boundary. No text is removed.
    """
    buffer, first = "", True
    pairs = {"（": "）", "(": ")", "[": "]", "【": "】", "“": "”", "‘": "’", '"': '"',
             "{": "}", "《": "》", "〈": "〉", "「": "」", "『": "』"}

    def boundaries(text):
        stack = []
        for i, char in enumerate(text):
            if stack and char == stack[-1]:
                stack.pop()
            elif char in pairs:
                stack.append(pairs[char])
            next_char = text[i+1:i+2]
            token = char.isascii() and (char.isalnum() or char in "._+-/%")
            next_token = bool(next_char) and next_char.isascii() and (next_char.isalnum() or next_char in "._+-/%")
            if not stack and not (token and next_token):
                yield i+1

    for delta in deltas:
        buffer += delta
        while buffer:
            safe = list(boundaries(buffer))
            punctuation = next((i for i in safe if buffer[i-1] in enders
                                and not (buffer[i-1] == "." and i == len(buffer))
                                and not (buffer[i-1] == "." and i < len(buffer)
                                         and buffer[i-2:i-1].isdigit() and buffer[i:i+1].isdigit())), None)
            cut = punctuation
            if first and limit and len(buffer) > limit and (cut is None or cut > limit):
                candidates = [i for i in safe if 8 <= i <= limit and i < len(buffer)]
                soft = [i for i in candidates if buffer[:i].endswith(
                    ("之后", "之前", "时候", "的话", "这样", "同时", " "))]
                if candidates:
                    cut = max(soft or candidates)
                else:
                    extended = [i for i in safe if i > limit and i < len(buffer)]
                    if extended:
                        cut = min(extended)
            if cut is None:
                break
            clause, buffer = buffer[:cut], buffer[cut:]
            if clause.strip():
                first = False
                yield clause
    if buffer.strip():
        yield buffer


def server_options(threads, batch_threads=None, cpu_range=None, batch_cpu_range=None):
    if threads < 1 or (batch_threads is not None and batch_threads < 1):
        raise ValueError("线程数必须为正整数")
    options = ["-t", str(threads)]
    if batch_threads is not None:
        options += ["--threads-batch", str(batch_threads)]
    for flag, value in [("--cpu-range", cpu_range), ("--cpu-range-batch", batch_cpu_range)]:
        if value:
            if not re.fullmatch(r"\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*", value):
                raise ValueError("CPU 范围格式无效")
            options += [flag, value]
    if cpu_range:
        options += ["--cpu-strict", "1"]
    if batch_cpu_range:
        options += ["--cpu-strict-batch", "1"]
    return options


def valid_speed(value):
    value = float(value)
    if not math.isfinite(value) or not 0.5 <= value <= 1.5:
        raise ValueError("语速须在 0.5 至 1.5 之间")
    return value


def warmup_pipeline(speech, chat, language, prompt):
    import numpy as np
    from robot import RATE, resample_audio

    started = time.perf_counter()
    text = "你好，这是语音预热。" if language == "zh" else "Hello, this is a warmup."
    audio = list(speech.synthesize(text))
    synthesized = time.perf_counter()
    speech.recognize(np.concatenate([resample_audio(a.samples, a.sample_rate, RATE) for a in audio]))
    recognized = time.perf_counter()
    # Exactly the production system prefix, but no Dialogue/history object.
    response = chat.request("/v1/chat/completions", {
        "messages": [{"role": "system", "content": prompt},
                     {"role": "user", "content": text}],
        "max_tokens": 1, "temperature": 0,
        "chat_template_kwargs": {"enable_thinking": False}, "cache_prompt": True,
    })
    finished = time.perf_counter()
    return {"tts_s": synthesized-started, "asr_s": recognized-synthesized,
            "llm_s": finished-recognized, "total_s": finished-started,
            "timings": response.get("timings", {})}


class SileroDetector:
    """Silero classifies speech; Endpoint alone owns trailing silence timing."""

    def __init__(self, model):
        from pathlib import Path
        import sherpa_onnx
        if not Path(model).is_file():
            raise FileNotFoundError(f"Silero VAD 模型不存在：{model}")
        config = sherpa_onnx.VadModelConfig()
        config.silero_vad.model = str(model)
        config.silero_vad.min_speech_duration = 0.08
        config.silero_vad.min_silence_duration = 0.032
        config.sample_rate = 16000
        config.num_threads = 1
        self.vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=30)

    def reset(self):
        self.vad.reset()

    def feed(self, samples):
        self.vad.accept_waveform(samples)
        detected = self.vad.is_speech_detected()
        while not self.vad.empty():
            self.vad.pop()
        return detected
