"""Offline desktop voice prototype. Movement commands are logged on this bench."""

import argparse
from collections import deque
from contextlib import contextmanager
import json
from math import gcd
import os
from pathlib import Path
import queue
import re
import subprocess
import threading
import time
from typing import NamedTuple
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener
import wave
from acceleration import split_first_clause, server_options, valid_speed, warmup_pipeline, SileroDetector, tts_model_path
from service_runner import notify_ready


ROOT = Path(__file__).resolve().parent
ASR = "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17"
TTS = "vits-melo-tts-zh_en"
ZH_LL = "sherpa-onnx-vits-zh-ll"
THERESA = "vits-zh-hf-theresa"
VOICES = {
    "zh": {"melo": (TTS, 0), **{f"zh-ll-{sid}": (ZH_LL, sid) for sid in range(5)},
           "theresa": (THERESA, 0)},
    "en": {"lessac": ("vits-piper-en_US-lessac-medium", "en_US-lessac-medium.onnx"),
           "ryan": ("piper-ryan", "en_US-ryan-low.onnx")},
}
DEFAULT_VOICES = {"zh": "melo", "en": "lessac"}
VOICE_SAMPLE = {
    "zh": "你好，我是你的桌面机器人。我们来聊聊今天的计划吧。",
    "en": "Hello, I'm your desktop robot. Let's talk about what you would like to do today.",
}
RATE = 16000
BLOCK = 320
COMMANDS = {
    "zh": {"前进": "FORWARD", "后退": "REVERSE", "左转": "LEFT",
           "右转": "RIGHT", "停止": "STOP"},
    "en": {"move forward": "FORWARD", "move backward": "REVERSE",
           "turn left": "LEFT", "turn right": "RIGHT", "stop moving": "STOP"},
}
END_COMMANDS = {"zh": "结束对话", "en": "end chat"}
ZH_PROMPT = (
    "你是桌面机器人，功能只有语音对话和短距离移动。"
    "用一句完整的口语中文直接回答用户当前的问题，不超过 30 个字，句子要说完整。"
    "结合本次对话的信息，人名和物品名沿用用户说过的说法。"
    "用户追问怎么做时给出具体做法，不要照抄上一句回答。听不清时简短确认。"
)
EN_PROMPT = (
    "You are a desktop robot. Your only abilities are talking and moving short distances. "
    "Reply in English with ONE short spoken sentence of at most 16 words. "
    "Answer the user's current question directly, keeping names and details from this conversation. "
    "If the user asks how to do something, give a concrete step instead of repeating your last sentence. "
    "Do not add a closing question."
)
PROMPTS = {"zh": ZH_PROMPT, "en": EN_PROMPT}
COMPACT_PROMPTS = {
    "zh": "你是只能聊天和短距离移动的桌面机器人。用一句完整口语中文回答，不超过30字。沿用上下文的人名和物品名，追问给具体做法，不重复旧答案；听不清就确认。",
    "en": "Reply in English as a desktop robot that only talks and moves short distances. Use one complete sentence within 16 words. Keep names and details from context; give concrete steps on follow-ups, without repeating or adding a closing question.",
}
CLAUSE_END = {"zh": "，。！？；", "en": ",.!?;"}


def split_clauses(deltas, enders):
    buffer = ""
    for delta in deltas:
        buffer += delta
        while buffer:
            cut = min((buffer.find(ch) for ch in enders if ch in buffer), default=-1)
            if cut < 0:
                break
            clause, buffer = buffer[:cut + 1], buffer[cut + 1:]
            if clause.strip():
                yield clause
    if buffer.strip():
        yield buffer


class SpokenAudio(NamedTuple):
    samples: object
    sample_rate: int


class Dialogue:
    def __init__(self, reply, language="zh", reply_stream=None, prompt_mode="original", first_clause_chars=16):
        self.reply = reply
        self.reply_stream = reply_stream
        self.language = language
        self.history = deque(maxlen=8)
        self.last_answer = ""
        self.prompt = (COMPACT_PROMPTS if prompt_mode == "compact" else PROMPTS)[language]
        self.first_clause_chars = first_clause_chars if language == "zh" else 0
        self.first_token_at = None

    def turn(self, text):
        kind, stream = self.turn_stream(text)
        if kind != "chat":
            return kind, stream or ""
        return kind, "".join(stream)

    def turn_stream(self, text):
        text = text.strip()
        command = " ".join(text.rstrip("。！？.!?").casefold().split())
        if not any(char.isalnum() for char in text):
            return "empty", None
        if command == END_COMMANDS[self.language]:
            self.history.clear()
            return "end", None
        if command in COMMANDS[self.language]:
            return "command", COMMANDS[self.language][command]
        user = {"role": "user", "content": text}
        self.first_token_at = None
        messages = [{"role": "system", "content": self.prompt}, *self.history, user]
        return "chat", self._clauses(messages, user)

    def _clauses(self, messages, user):
        deltas = self.reply_stream(messages) if self.reply_stream else iter([self.reply(messages)])
        parts = []

        def capture():
            for delta in deltas:
                if self.first_token_at is None:
                    self.first_token_at = time.perf_counter()
                parts.append(delta)
                yield delta

        yield from split_first_clause(capture(), CLAUSE_END[self.language], self.first_clause_chars)
        answer = "".join(parts).strip()
        if not answer:
            raise RuntimeError("对话模型返回了空回复")
        self.last_answer = answer
        self.history.extend((user, {"role": "assistant", "content": answer}))


class Endpoint:
    def __init__(self, silence_seconds=0.7):
        if not 0.2 <= silence_seconds <= 1.5:
            raise ValueError("结束静音须在 0.2 至 1.5 秒之间")
        self.silence_seconds = silence_seconds
        self.first_voice = None
        self.last_voice = None

    def feed(self, voiced, elapsed):
        if self.first_voice is None and elapsed >= 15:
            return "idle"
        if voiced:
            if self.first_voice is None:
                self.first_voice = elapsed
            self.last_voice = elapsed
        if self.first_voice is None:
            return "listen"
        if elapsed - self.first_voice >= 12 or elapsed - self.last_voice >= self.silence_seconds:
            return "done"
        return "listen"


def resolve_voice(assets, language, override=None):
    settings_path = assets / "voices.json"
    name = override
    if name is None:
        settings = json.loads(settings_path.read_text(encoding="utf-8-sig")) if settings_path.is_file() else {}
        if not isinstance(settings, dict):
            raise ValueError(f"{settings_path} 需要是 JSON 对象")
        name = settings.get(language, DEFAULT_VOICES[language])
    if not isinstance(name, str) or name not in VOICES[language]:
        raise ValueError(f"{language} 模式不支持音色 {name!r}，可选：{', '.join(VOICES[language])}")
    return name


class Voice:
    def __init__(self, assets, threads, language, name, tts_threads=None, speed=None):
        self.language = language
        self.speed = valid_speed(speed if speed is not None else (0.9 if name == "theresa" else 1.0))
        threads = tts_threads or threads
        folder, voice = VOICES[language][name]
        tts = assets / folder
        if language == "en":
            from piper import PiperVoice

            self.tts = PiperVoice.load(tts / voice)
            return

        import sherpa_onnx

        self.speaker_id = voice
        model_path = tts_model_path(tts)
        for name in ("tokens.txt", "lexicon.txt", "dict"):
            if not (tts / name).exists():
                raise FileNotFoundError(tts / name)
        rules = ",".join(str(path) for path in sorted(tts.glob("*.fst")))
        model = sherpa_onnx.OfflineTtsVitsModelConfig(
            model=str(model_path), tokens=str(tts / "tokens.txt"),
            lexicon=str(tts / "lexicon.txt"), dict_dir=str(tts / "dict"),
        )
        self.tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(vits=model, num_threads=threads),
            rule_fsts=rules, max_num_sentences=1,
        ))

    def synthesize(self, text):
        if self.language == "en":
            from piper.config import SynthesisConfig
            for chunk in self.tts.synthesize(text, syn_config=SynthesisConfig(length_scale=1.0/self.speed)):
                yield SpokenAudio(chunk.audio_float_array, chunk.sample_rate)
            return
        for sentence in re.split(r"(?<=[。！？；])", text):
            if sentence.strip():
                yield self.tts.generate(sentence, sid=self.speaker_id, speed=self.speed)


class Speech:
    def __init__(self, assets, threads, language="zh", voice=None, tts_threads=None, speed=None):
        import sherpa_onnx

        name = resolve_voice(assets, language, voice)
        asr = assets / ASR
        for path in (asr / "model.int8.onnx", asr / "tokens.txt"):
            if not path.is_file():
                raise FileNotFoundError(path)
        self.recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=str(asr / "model.int8.onnx"), tokens=str(asr / "tokens.txt"),
            language=language, use_itn=True, num_threads=threads,
        )
        self.voice = Voice(assets, threads, language, name, tts_threads, speed)

    def recognize(self, samples):
        stream = self.recognizer.create_stream()
        stream.accept_waveform(RATE, samples)
        self.recognizer.decode_stream(stream)
        return stream.result.text.strip()

    def synthesize(self, text):
        return self.voice.synthesize(text)


class LocalChat:
    def __init__(self, port):
        self.url = f"http://127.0.0.1:{port}"
        self.opener = build_opener(ProxyHandler({}))
        self.metrics = {}

    def request(self, path, data=None, timeout=60):
        body = None if data is None else json.dumps(data).encode()
        request = Request(self.url + path, body, {"Content-Type": "application/json"})
        with self.opener.open(request, timeout=timeout) as response:
            return json.load(response)

    def chat_body(self, messages, stream=False):
        body = {
            "messages": messages,
            "max_tokens": 48,
            "temperature": 0.5,
            "repeat_penalty": 1.1,
            "chat_template_kwargs": {"enable_thinking": False},
            "cache_prompt": True,
        }
        if stream:
            body["stream"] = True
        if getattr(self, "seed", None) is not None:
            body["seed"] = self.seed
        return body

    def reply(self, messages):
        response = self.request("/v1/chat/completions", self.chat_body(messages))
        answer = response["choices"][0]["message"]["content"].strip()
        if not answer:
            raise RuntimeError("对话模型返回了空回复")
        return answer

    def reply_stream(self, messages):
        self.metrics = {}
        body = json.dumps(self.chat_body(messages, stream=True)).encode()
        request = Request(self.url + "/v1/chat/completions", body, {"Content-Type": "application/json"})
        with self.opener.open(request, timeout=60) as response:
            for line in response:
                if not line.startswith(b"data:"):
                    continue
                payload = line[5:].strip()
                if payload == b"[DONE]":
                    return
                item = json.loads(payload)
                if "timings" in item:
                    self.metrics.update(item["timings"])
                choices = item.get("choices", [])
                delta = choices[0].get("delta", {}).get("content") if choices else None
                if delta:
                    yield delta


@contextmanager
def local_server(executable, assets, port, threads, batch_threads=None, cpu_range=None,
                 batch_cpu_range=None, model_path=None):
    model = Path(model_path).resolve() if model_path else assets / "chat.gguf"
    for path in (executable, model):
        if not path.is_file():
            raise FileNotFoundError(path)
    log_path = assets / "llama.log"
    with log_path.open("wb") as log:
        process = subprocess.Popen([
            str(executable), "-m", str(model), "--host", "127.0.0.1",
            "--port", str(port), "-c", "2048", "-np", "1",
            *server_options(threads, batch_threads, cpu_range, batch_cpu_range),
        ], stdout=log, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        try:
            chat = LocalChat(port)
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"本地模型进程退出，见 {log_path}")
                try:
                    if chat.request("/health", timeout=1).get("status") == "ok":
                        break
                except (URLError, TimeoutError):
                    pass
                time.sleep(0.25)
            else:
                raise RuntimeError(f"等待模型加载超时，见 {log_path}")
            yield chat
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def audio_format(preferred_rate, native_rate, max_channels, supported):
    for rate in dict.fromkeys((preferred_rate, int(native_rate))):
        for channels in range(1, min(max_channels, 2) + 1):
            if supported(rate, channels):
                return rate, channels
    raise RuntimeError("音频设备无法以单声道或双声道打开，请检查设备编号和系统音频设置")


def resample_audio(samples, source_rate, target_rate):
    import numpy as np

    samples = np.asarray(samples, dtype="float32")
    if source_rate == target_rate:
        return samples
    from scipy.signal import resample_poly

    divisor = gcd(source_rate, target_rate)
    return resample_poly(samples, target_rate // divisor, source_rate // divisor)


def device_format(device, kind, preferred_rate):
    import sounddevice as sd

    info = sd.query_devices(device, kind=kind)
    check = sd.check_input_settings if kind == "input" else sd.check_output_settings

    def supported(rate, channels):
        try:
            check(device=device, samplerate=rate, channels=channels, dtype="float32")
            return True
        except sd.PortAudioError:
            return False

    return audio_format(preferred_rate, info["default_samplerate"],
                        info[f"max_{kind}_channels"], supported)


def play_audio(samples, source_rate, device):
    import numpy as np
    import sounddevice as sd

    rate, channels = device_format(device, "output", source_rate)
    samples = resample_audio(samples, source_rate, rate)
    if channels == 2:
        samples = np.repeat(samples[:, None], 2, axis=1)
    sd.play(samples, rate, device=device)
    started = time.perf_counter()
    sd.wait()
    return started


def check_audio(input_device, output_device):
    import sounddevice as sd

    rate, channels = device_format(input_device, "input", RATE)
    print(f"请说话，正在录音 3 秒（{rate} Hz，{channels} 声道）……", flush=True)
    recording = sd.rec(3 * rate, samplerate=rate, channels=channels, dtype="float32",
                       device=input_device, blocking=True)
    print("正在回放……", flush=True)
    play_audio(recording.mean(axis=1), rate, output_device)


def listen(device, threshold, silence_seconds=0.7, detector=None):
    import numpy as np
    import sounddevice as sd

    endpoint = Endpoint(silence_seconds)
    if detector is not None:
        detector.reset()
    # Silero's onset confirmation can exceed 200 ms; retain the word onset.
    preroll = deque(maxlen=25 if detector is not None else 10)
    chunks = []
    voiced_blocks = 0
    rate, channels = device_format(device, "input", RATE)
    block = round(rate * BLOCK / RATE)
    with sd.InputStream(samplerate=rate, channels=channels, dtype="float32",
                        blocksize=block, device=device) as stream:
        started = time.perf_counter()
        while True:
            audio, overflow = stream.read(block)
            if overflow:
                raise RuntimeError("麦克风缓冲溢出，请重试")
            elapsed = time.perf_counter() - started
            voiced = (detector.feed(resample_audio(audio.mean(axis=1), rate, RATE))
                      if detector is not None else np.sqrt(np.mean(audio ** 2)) >= threshold)
            voiced_blocks = voiced_blocks + 1 if voiced else 0
            if endpoint.first_voice is None:
                preroll.append(audio)
                voiced = voiced_blocks >= 3
                if voiced:
                    chunks.extend(preroll)
            else:
                chunks.append(audio)
            state = endpoint.feed(voiced, elapsed)
            if state == "idle":
                return None, None
            if state == "done":
                mono = np.concatenate(chunks).mean(axis=1)
                return resample_audio(mono, rate, RATE), started + endpoint.last_voice


def read_wav(path):
    import numpy as np

    with wave.open(str(path), "rb") as file:
        if (file.getframerate(), file.getnchannels(), file.getsampwidth()) != (RATE, 1, 2):
            raise ValueError(f"{path} 需要 16 kHz 单声道 16 位 PCM WAV")
        return np.frombuffer(file.readframes(file.getnframes()), "<i2").astype("float32") / 32768


def save_wav(path, samples, rate):
    import numpy as np

    with wave.open(str(path), "wb") as file:
        file.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        pcm = (np.clip(samples, -1, 1) * 32767).astype("<i2")
        file.writeframes(pcm.tobytes())


def run_turn(dialogue, speech, samples, speech_end, output=None, device=None, metrics_path=None):
    start = time.perf_counter()
    text = speech.recognize(samples)
    recognized = time.perf_counter()
    kind, stream = dialogue.turn_stream(text)
    print(f"你  {text or '（未识别）'}", flush=True)
    if kind == "command":
        print(f"台架模拟动作  {stream}", flush=True)
    elif kind == "chat":
        clauses, clips = queue.Queue(), queue.Queue()
        state = {"first": None, "last": None, "gen": None, "text": None, "tts_start": None, "error": None}

        def generate():
            try:
                for clause in stream:
                    if state["text"] is None:
                        state["text"] = time.perf_counter()
                    clauses.put(clause)
                state["gen"] = time.perf_counter()
            except Exception as error:
                state["error"] = error
            finally:
                clauses.put(None)

        def synthesize():
            try:
                while True:
                    clause = clauses.get()
                    if clause is None:
                        break
                    if state["tts_start"] is None:
                        state["tts_start"] = time.perf_counter()
                    for audio in speech.synthesize(clause):
                        now = time.perf_counter()
                        if state["first"] is None:
                            state["first"] = now
                        state["last"] = now
                        clips.put(audio)
            except Exception as error:
                state["error"] = state["error"] or error
            finally:
                clips.put(None)

        threading.Thread(target=generate, daemon=True).start()
        threading.Thread(target=synthesize, daemon=True).start()
        collected = []
        playback_start = None
        while True:
            audio = clips.get()
            if audio is None:
                break
            collected.append(audio)
            if output is None:
                started = play_audio(audio.samples, audio.sample_rate, device)
                if playback_start is None:
                    playback_start = started
        if state["error"] is not None:
            raise state["error"]
        if not collected:
            raise RuntimeError("语音合成没有生成音频")
        print(f"机器人  {dialogue.last_answer}", flush=True)
        if output:
            import numpy as np

            save_wav(output, np.concatenate([audio.samples for audio in collected]),
                     collected[0].sample_rate)
        base = speech_end if speech_end is not None else start
        first_ready = playback_start if output is None else state["first"]
        print(f"识别 {recognized-start:.2f}s | 生成 {state['gen']-recognized:.2f}s | "
              f"首声 {state['first']-recognized:.2f}s | 整段 {state['last']-recognized:.2f}s | "
              f"{'文件输入到首声' if output else '说完到出声'} {first_ready-base:.2f}s | "
              f"整段等待 {state['last']-base:.2f}s", flush=True)
        owner = getattr(dialogue.reply_stream, "__self__", None)
        row = {
            "event": "turn", "input_kind": "file" if output else "microphone",
            "text": text, "answer": dialogue.last_answer,
            "endpoint_wait_s": None if speech_end is None else start-speech_end,
            "asr_s": recognized-start,
            "first_token_s": None if dialogue.first_token_at is None else dialogue.first_token_at-recognized,
            "first_clause_s": state["text"]-recognized,
            "first_synthesis_s": state["first"]-state["tts_start"],
            "first_audio_ready_s": state["first"]-recognized,
            "playback_delay_s": None if playback_start is None else playback_start-state["first"],
            "response_s": first_ready-base,
            "total_s": time.perf_counter()-base,
            "llm": getattr(owner, "metrics", {}),
        }
        if metrics_path:
            with Path(metrics_path).open("a", encoding="utf8") as file:
                file.write(json.dumps(row, ensure_ascii=False)+"\n")
        print("阶段计时 " + json.dumps(row, ensure_ascii=False), flush=True)
    return kind


def serve_conversations(args,chat,speech,detector):
    import numpy as np
    chime=(0.12*np.sin(2*np.pi*660*np.arange(4800)/48000)).astype('float32')
    if args.auto_listen:
        play_audio(chime,48000,args.output_device)
    notify_ready(args.ready_file)
    while True:
        if not args.auto_listen:
            input('按 Enter 模拟唤醒，Ctrl+C 退出。')
            play_audio(chime,48000,args.output_device)
        dialogue=Dialogue(chat.reply,args.language,chat.reply_stream,args.prompt_mode,args.first_clause_chars)
        while True:
            print('正在听……',flush=True)
            samples,speech_end=listen(args.input_device,args.threshold,args.silence,detector)
            if samples is None:
                print('会话已超时，等待下一句。',flush=True)
                break
            kind=run_turn(dialogue,speech,samples,speech_end,device=args.output_device,metrics_path=args.metrics)
            if kind=='end':break


def main():
    parser = argparse.ArgumentParser(description="桌面机器人离线语音台架")
    parser.add_argument("--language", choices=PROMPTS, default="zh", help="zh 中文，en 英文")
    parser.add_argument("--voice", help="本次使用的音色，优先于 voices.json")
    parser.add_argument("--list-voices", action="store_true", help="列出中英文音色")
    parser.add_argument("--preview-voice", type=Path, metavar="WAV", help="生成选中音色的试听 WAV")
    parser.add_argument("--devices", action="store_true", help="列出音频设备")
    parser.add_argument("--audio-check", action="store_true", help="录音三秒并回放，无需加载模型")
    parser.add_argument("--input-device", type=int)
    parser.add_argument("--output-device", type=int)
    parser.add_argument("--threshold", type=float, default=0.012, help="麦克风语音 RMS 门限")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--tts-threads", type=int, help="语音合成线程数，默认与 --threads 相同")
    parser.add_argument("--speed", type=float, help="语速 0.5–1.5；Theresa 默认 0.9，其余 1.0")
    parser.add_argument("--batch-threads", type=int)
    parser.add_argument("--cpu-range")
    parser.add_argument("--batch-cpu-range")
    parser.add_argument("--model", type=Path, help="可选 GGUF，不覆盖默认模型")
    parser.add_argument("--prompt-mode", choices=("original", "compact"), default="original")
    parser.add_argument("--first-clause-chars", type=int, choices=(0, 16), default=16)
    parser.add_argument("--no-warmup", action="store_true")
    parser.add_argument("--silence", type=float, default=0.7)
    parser.add_argument("--vad", choices=("rms", "silero"), default="rms")
    parser.add_argument("--vad-model", type=Path)
    parser.add_argument("--metrics", type=Path, help="追加 JSONL 分段计时日志")
    parser.add_argument("--auto-listen", action="store_true", help="无屏模式：加载后直接听，空闲不读键盘、不重复提示音")
    parser.add_argument("--ready-file", type=Path, help="模型和音频就绪后写入状态，供开机服务检查")
    parser.add_argument("--port", type=int, default=17860)
    parser.add_argument("--assets", type=Path, default=ROOT / ".local")
    parser.add_argument("--server", type=Path, help="llama-server 可执行文件")
    parser.add_argument("--wav", nargs="+", type=Path, help="依次输入 WAV，模拟一次多轮会话")
    args = parser.parse_args()
    if args.list_voices:
        for language, voices in VOICES.items():
            print(f"{language} ({DEFAULT_VOICES[language]} 为默认): {', '.join(voices)}")
        return
    if args.devices:
        import sounddevice as sd

        print(sd.query_devices())
        return
    if args.audio_check:
        check_audio(args.input_device, args.output_device)
        return
    assets = args.assets.resolve()
    voice = resolve_voice(assets, args.language, args.voice)
    if args.preview_voice:
        import numpy as np

        engine = Voice(assets, args.threads, args.language, voice, args.tts_threads, args.speed)
        clips = list(engine.synthesize(VOICE_SAMPLE[args.language]))
        if not clips or not any(len(clip.samples) for clip in clips):
            raise RuntimeError("语音合成没有生成音频")
        save_wav(args.preview_voice, np.concatenate([clip.samples for clip in clips]), clips[0].sample_rate)
        print(f"{voice} 试听文件：{args.preview_voice}")
        return
    binary = "llama-server.exe" if os.name == "nt" else "llama-server"
    executable = args.server.resolve() if args.server else assets / "llama" / binary
    print(f"正在加载离线模型（{args.language} / {voice}）……", flush=True)
    speech = Speech(assets, args.threads, args.language, voice, args.tts_threads, args.speed)
    detector = SileroDetector(args.vad_model or assets / "silero_vad.onnx") if args.vad == "silero" else None
    prompt = (COMPACT_PROMPTS if args.prompt_mode == "compact" else PROMPTS)[args.language]
    def dialogue_factory():
        return Dialogue(chat.reply, args.language, chat.reply_stream, args.prompt_mode, args.first_clause_chars)
    with local_server(executable, assets, args.port, args.threads, args.batch_threads,
                      args.cpu_range, args.batch_cpu_range, args.model) as chat:
        if not args.no_warmup:
            print("静默预热 " + json.dumps(warmup_pipeline(speech, chat, args.language, prompt), ensure_ascii=False), flush=True)
        if args.wav:
            dialogue = dialogue_factory()
            for index, path in enumerate(args.wav, 1):
                prefix = "reply" if args.language == "zh" else "reply-en"
                output = assets / f"{prefix}-{index:02d}.wav"
                output.unlink(missing_ok=True)
                run_turn(dialogue, speech, read_wav(path), None, output=output, metrics_path=args.metrics)
            return
        serve_conversations(args,chat,speech,detector)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        pass
    except (OSError, ValueError, RuntimeError) as error:
        raise SystemExit(f"运行失败：{error}") from error
