# 离线对话加速与验收

> 当前阶段总览见[第一阶段主文档](phase-1-offline-bilingual.md)。下面的命令用于手动调试，执行前先`sudo systemctl stop desktop-robot.service`，结束后再恢复服务；日常开机自动运行，无需按Enter。旧长测使用1.716GHz条件，现已按用户要求解除人工上限，新配置长测尚待完成。

本轮保持 Orange Pi 4 Pro A733、Qwen3-1.7B、SenseVoice 和 Theresa。
所有时间均区分文件输入、麦克风输入和实际播放；文件测试不是真人验收。

## 启动

```bash
cd ~/desktop-robot
.venv/bin/python run_fast.py --language zh --metrics .local/human-fast-zh.jsonl
.venv/bin/python run_fast.py --language en --metrics .local/human-fast-en.jsonl
```

按 Enter 开始会话；提示音结束后说话。播报结束自动继续听，15 秒无语音退出会话。
中文结束口令为整句“结束对话”，英文为 `End chat`。Ctrl+C 退出程序。
目前设备编号 0 为 USB 麦克风、3 为 USB 音箱；重插或换 USB 口后先运行
`robot.py --devices` 核对，并更新 `fast-profile.json`。

Theresa 默认实际语速为 0.9，其他音色默认 1.0，可用 `--speed 0.85` 覆盖。
减慢语速不计作加速。保存的 `.local/voices.json` 继续分别控制中英文音色。

## 对照开关

- `--no-warmup`：关闭静默预热以测冷首轮。生产启动先完成 TTS、ASR 和固定系统提示预热，预热不会进入会话历史，也不会播放声音。
- `--batch-threads N --batch-cpu-range RANGE`：独立设置输入处理线程与核范围。生成固定两大核。使用原生 `.local/llama/llama-server`，不能套用只允许两核的旧 `llama-big.sh` 来测试其他核。
- `--prompt-mode original|compact`：原始提示和压缩提示对照；历史长度和最大输出 token 数不变。
- `--first-clause-chars 16|0`：中文首段提前切分或仅按标点切分。16 是软上限，数字、英文单词和括号引号跨度受保护时允许超过；英文保持按标点切分。
- `--vad rms|silero --silence 0.45|0.55|0.70`：对比语音检测和结束静音时长。Silero 需要 `.local/silero_vad.onnx`；缺失时明确失败，不偷偷回退。
- `--model PATH`：使用候选 GGUF，不覆盖 `.local/chat.gguf`。
- `--metrics PATH`：追加每轮 JSONL，包括端点等待、ASR、首 token、首文本段、首段合成、播放开销、模型 prompt/cache/decode 指标和整轮耗时。
- `bench.py --input-cache DIR`：首次保存合成输入，后续从同一PCM文件重放，避免换模型或音色时连输入一起改变。现有探针可用 `--inputs-dir` 重用同一套输入。

`response_s` 对麦克风为最后检测到语音至调用播放的时间；包含端点等待。
对文件则为文件开始处理至第一段音频就绪，不能与真人数值直接混用。
软件播放时间不是物理麦克风测出的扬声器发声时间；音频缓冲仍需真人验证。

## 测试工具

```bash
.venv/bin/python -m unittest discover -p 'test_*.py' -v
.venv/bin/python speed_probe.py --cases cold,warm,batch4,batch8 --output .local/new-ab-run
.venv/bin/python vad_compare.py
.venv/bin/python run_fast.py --bench --language zh --gap 8 --metrics .local/new-zh.jsonl
sudo bash offline-speed-check.sh --duration 1800 --output /home/orangepi/desktop-robot/.local/new-offline-run
```

每个探针目录必须使用新名称，以免覆盖证据。A/B 使用缓存的相同输入，第一条来自已授权的真人录音，其他条目是合成语音；不自动录制麦克风。
VAD 对照含 0.3/0.5 秒句中停顿及纯静音；它不能代替实际环境下的误触发/截断测试。

断网测试使用临时网络命名空间，只有回环及无路由的虚拟接口，测试进程无法使用宿主的以太网和 Wi-Fi，SSH 仍可操作。
日志保留起始网络状态、结束状态、各轮退出码、每 5 秒温度和频率。
这证明程序进程树可离线运行，不等于已经完成整机拔线、关闭 Wi-Fi、冷启动后的真人验收。
30 分钟测试连续交替中英文合成输入，不播放音箱；真人音箱稳定性与听感单独验收。

## 回退

本地与板端 `.local/speed-rollback-20261111/` 保留本轮修改前的程序。
停止机器人后，将该目录 `robot.py`、`bench.py` 恢复到项目根；板端 `voices.json` 与 `llama-big.sh` 的备份分别恢复到 `.local/`。
新增模块可以保留，旧程序不引用它。保留日志与候选模型，不删除原始模型。

## 官方参考

- [llama.cpp server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)：输入处理/生成独立线程与核范围、缓存、SSE。板端版本 b12119，先用本机 `--help` 核对支持参数；不自动升级二进制。
- [Qwen3](https://github.com/QwenLM/Qwen3)：非思考对话与不同模型规模；本项目原先已关闭思考。
- [sherpa-onnx VAD](https://github.com/k2-fsa/sherpa-onnx/blob/master/python-api-examples/vad-microphone.py)：Silero 语音活动检测。
- [sherpa-onnx TTS](https://github.com/k2-fsa/sherpa-onnx/blob/master/python-api-examples/offline-tts-play.py)：实际语速和播放队列。句级回调不等于音频逐帧流式。
- [Rockchip RKNN](https://github.com/airockchip/rknn-toolkit2)：支持范围不是全志 A733，本轮不采用 RK3588 的 NPU 部署路线。

## 结果

本轮实测结论和未完成的物理验收见 `speed-results.md`；没有日志的项目一律未测。
