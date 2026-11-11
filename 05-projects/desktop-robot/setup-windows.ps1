$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
New-Item -ItemType Directory -Force -Path .local | Out-Null

function Get-Asset($Url, $Target, $Sha256 = '') {
    if (Test-Path -LiteralPath $Target) {
        if ($Sha256 -and (Get-FileHash -LiteralPath $Target).Hash -ne $Sha256) {
            throw "Existing asset failed SHA-256: $Target"
        }
        return
    }
    $temporary = "$Target.download"
    Write-Host "Downloading $Target (resumes existing partial file)"
    curl.exe --fail --location --progress-bar --show-error --retry 2 --connect-timeout 20 --max-time 900 --continue-at - -o $temporary $Url
    if ($LASTEXITCODE -ne 0) { throw "Download failed: $Url" }
    if ($Sha256 -and (Get-FileHash -LiteralPath $temporary).Hash -ne $Sha256) {
        throw "Downloaded asset failed SHA-256: $Target"
    }
    Move-Item -LiteralPath $temporary -Destination $Target
}

uv --system-certs venv --allow-existing --python 3.12 .venv
if ($LASTEXITCODE -ne 0) { throw 'Could not create Python environment' }
uv --system-certs pip install --python .venv/Scripts/python.exe -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Could not install Python dependencies' }

$asr = 'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17'
$tts = 'vits-melo-tts-zh_en'
if (-not (Test-Path ".local/$asr/model.int8.onnx")) {
    Get-Asset "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/$asr.tar.bz2" '.local/asr.tar.bz2'
    tar.exe -xf .local/asr.tar.bz2 -C .local
    if ($LASTEXITCODE -ne 0) { throw 'Could not extract SenseVoice' }
}
if (-not (Test-Path ".local/$tts/model.onnx")) {
    Get-Asset "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/$tts.tar.bz2" '.local/tts.tar.bz2'
    tar.exe -xf .local/tts.tar.bz2 -C .local
    if ($LASTEXITCODE -ne 0) { throw 'Could not extract MeloTTS' }
}
$ttsEn = 'vits-piper-en_US-lessac-medium'
Get-Asset "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/$ttsEn.tar.bz2" '.local/tts-en.tar.bz2' '9e3febfacf0abf4270172d2958bcec246032b7e88efc2720840cc80c93de334e'
if (-not (Test-Path ".local/$ttsEn/en_US-lessac-medium.onnx") -or
    -not (Test-Path ".local/$ttsEn/en_US-lessac-medium.onnx.json")) {
    tar.exe -xf .local/tts-en.tar.bz2 -C .local
    if ($LASTEXITCODE -ne 0) { throw 'Could not extract the Piper English voice' }
}
$ttsZhLl = 'sherpa-onnx-vits-zh-ll'
Get-Asset "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/$ttsZhLl.tar.bz2" '.local/tts-zh-ll.tar.bz2' 'f7393d1bbc59709d5f52ea76cd5bceeec62f6a29f9c1f79ff64b4c15ec841f3a'
if (-not (Test-Path ".local/$ttsZhLl/model.onnx")) {
    tar.exe -xf .local/tts-zh-ll.tar.bz2 -C .local
    if ($LASTEXITCODE -ne 0) { throw 'Could not extract the Chinese speaker model' }
}
$ryan = 'https://huggingface.co/rhasspy/piper-voices/resolve/b145f2ac26522d6a2ccde0164b7b0e48b1e3199c/en/en_US/ryan/low'
New-Item -ItemType Directory -Force -Path .local/piper-ryan | Out-Null
Get-Asset "$ryan/en_US-ryan-low.onnx" '.local/piper-ryan/en_US-ryan-low.onnx' '8d21a085cc4c0010f1f3e91d5008c8691277ccfa744eb0d747becd33a3444baf'
Get-Asset "$ryan/en_US-ryan-low.onnx.json" '.local/piper-ryan/en_US-ryan-low.onnx.json'
Get-Asset "$ryan/MODEL_CARD" '.local/piper-ryan/MODEL_CARD'
if (-not (Test-Path -LiteralPath '.local/voices.json')) {
    Copy-Item -LiteralPath 'voices.example.json' -Destination '.local/voices.json'
}
if (-not (Test-Path '.local/llama/llama-server.exe')) {
    Get-Asset 'https://github.com/ggml-org/llama.cpp/releases/download/b12119/llama-b12119-bin-win-cpu-x64.zip' '.local/llama.zip' '37a6c6c9eae5b7baa2619cba513781fad15ca0f63f7d07362ec83a294cf96f86'
    Expand-Archive .local/llama.zip .local/llama -Force
}
Get-Asset 'https://modelscope.cn/api/v1/models/ggml-org/Qwen3-1.7B-GGUF/repo?Revision=master&FilePath=Qwen3-1.7B-Q4_K_M.gguf' '.local/chat.gguf' 'd2387ca2dbfee2ffabce7120d3770dadca0b293052bc2f0e138fdc940d9bc7b5'
.venv/Scripts/python.exe -m unittest -v
if ($LASTEXITCODE -ne 0) { throw 'Bench tests failed' }
