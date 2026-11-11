#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

if [[ "$(uname -m)" != aarch64 ]] || ! python3 -c 'import sys; assert sys.version_info[:2] == (3, 11)'; then
    echo "需要 ARM64 Debian 12 和 Python 3.11。" >&2
    exit 1
fi
for tool in c++ make arecord aplay; do
    if ! command -v "$tool" >/dev/null; then
        echo "缺少 $tool，请先按部署指南安装 Debian 系统依赖。" >&2
        exit 1
    fi
done

sha256sum -c SHA256SUMS
tar -xzf .local/uv-arm64.tar.gz -C .local uv-aarch64-unknown-linux-gnu/uv
uv=.local/uv-aarch64-unknown-linux-gnu/uv
"$uv" --offline venv --allow-existing --no-python-downloads --python /usr/bin/python3 .venv
"$uv" --offline pip install --python .venv/bin/python --no-index --only-binary=:all: \
    --find-links .local/arm64-wheels -r requirements-arm64.txt
"$uv" pip check --python .venv/bin/python
.venv/bin/python -m unittest -v

for archive in asr tts tts-en tts-zh-ll; do
    tar -xjf ".local/$archive.tar.bz2" -C .local
done
if [[ ! -e .local/voices.json ]]; then
    cp voices.example.json .local/voices.json
fi
tar -xzf .local/llama-source.tar.gz -C .local
.venv/bin/cmake -S .local/llama.cpp-b12119 -B .local/llama-build \
    -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
    -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_APP=OFF \
    -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF -DLLAMA_OPENSSL=OFF \
    -DLLAMA_BUILD_NUMBER=12119 -DLLAMA_BUILD_COMMIT=6f1e65437
.venv/bin/cmake --build .local/llama-build --target llama-server --parallel 2
install -Dm755 .local/llama-build/bin/llama-server .local/llama/llama-server
.local/llama/llama-server --version
.venv/bin/python robot.py --devices
echo "安装完成。接好麦克风和音箱后运行 robot.py --audio-check。"
