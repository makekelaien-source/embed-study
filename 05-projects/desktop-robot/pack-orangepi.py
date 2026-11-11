"""Package the verified voice assets and ARM64 dependencies for Orange Pi."""

import hashlib
import io
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / ".local"
PINNED = {
    ".local/vits-zh-hf-theresa.tar.bz2": "f337638c49689e1d87135c4e224daa1aacc0109e784b1cf78eafb1b14a1d9e92",
    ".local/silero_vad.onnx": "9e2449e1087496d8d4caba907f23e0bd3f78d91fa552479bb9c23ac09cbb1fd6",
    ".local/chat.gguf": "d2387ca2dbfee2ffabce7120d3770dadca0b293052bc2f0e138fdc940d9bc7b5",
    ".local/llama-source.tar.gz": "f50c0a276ce7f653ae3ae10d0b940a7007b56885b845a1a920b504afaa7ab6a7",
    ".local/uv-arm64.tar.gz": "3ccfb6af6e242433eb552f7d9676abd5412c6595c497e990d9c8cb7b5bd4d2c3",
    ".local/tts-en.tar.bz2": "9e3febfacf0abf4270172d2958bcec246032b7e88efc2720840cc80c93de334e",
    ".local/tts-zh-ll.tar.bz2": "f7393d1bbc59709d5f52ea76cd5bceeec62f6a29f9c1f79ff64b4c15ec841f3a",
    ".local/piper-ryan/en_US-ryan-low.onnx": "8d21a085cc4c0010f1f3e91d5008c8691277ccfa744eb0d747becd33a3444baf",
}


def main():
    wheels = sorted((ASSETS / "arm64-wheels").glob("*.whl"))
    if len(wheels) != 19:
        raise RuntimeError("Expected 19 ARM64/universal wheels in .local/arm64-wheels")
    files = [ROOT / name for name in (
        "robot.py", "acceleration.py", "test_robot.py", "test_acceleration.py", "bench.py", "requirements-arm64.txt",
        "run_fast.py", "fast-profile.json", "speed_probe.py", "vad_compare.py", "summarize_speed.py",
        "speed_acceptance.py", "offline-speed-check.sh", "speed-tuning.md",
        "service_runner.py", "restore_frequency.py", "test_service.py",
        "desktop-robot.service", "desktop-robot-frequency.service", "autostart.md",
        "setup-orangepi.sh", "orangepi-setup.md", "voices.example.json", ".local/asr.tar.bz2",
        ".local/tts.tar.bz2", ".local/piper-ryan/en_US-ryan-low.onnx.json",
        ".local/piper-ryan/MODEL_CARD", *PINNED,
    )] + wheels
    sums = []
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if relative in PINNED and digest != PINNED[relative]:
            raise RuntimeError(f"SHA-256 mismatch: {relative}")
        sums.append(f"{digest}  {relative}\n")
    output = ASSETS / "desktop-robot-orangepi4pro.tar"
    partial = output.with_suffix(".part")
    with tarfile.open(partial, "w", format=tarfile.PAX_FORMAT) as archive:
        for path in files:
            archive.add(path, f"desktop-robot/{path.relative_to(ROOT).as_posix()}")
        manifest = "".join(sums).encode("ascii")
        info = tarfile.TarInfo("desktop-robot/SHA256SUMS")
        info.size = len(manifest)
        archive.addfile(info, io.BytesIO(manifest))
    partial.replace(output)
    print(output)


if __name__ == "__main__":
    main()
