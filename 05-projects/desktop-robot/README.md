# 离线语音桌面机器人

**第一阶段主入口：[跑通香橙派离线双语](phase-1-offline-bilingual.md)。** 当前配置、日常操作、已验证结果和未完成验收统一见该文档；下方早期安装/手动台架说明保留用于追溯。

当前目录包含电脑语音台架及香橙派 4 Pro 6GB 的部署准备。写卡、首次 SSH、迁移和上板验收见 [香橙派部署指南](orangepi-setup.md)。ESP32-S3 唤醒、两轮控制、USB-C 充电及打印外壳按后续实物阶段分别验收。

从第一批采购到装壳和整机验收，见[全流程建造清单](build-runbook.md)。

真人等待时间优化、当前香橙派启动配置、回退和分段计时见[加速操作说明](speed-tuning.md)，本轮证据和未通过项见[加速实测](speed-results.md)。历史基准使用的音色、语速和计时口径不同，不能直接代替当前真人验收。

已完成 64GB SD 系统卡写入与回读校验。接独立显示器、首次登录和 Wi-Fi 配置见[首次启动操作清单](first-boot-display.md)。

车头视觉和表情屏见[视觉与表情屏执行清单](vision-face-runbook.md)。[视觉诊断](vision_check.py)支持回放图片和采样摄像头，[前进联锁](forward_guard.c)可在电脑上编译测试，[表情素材导出](face_screen.py)可将内置表情或自备角色 PNG 转为 240×320 彩屏素材。实车运行按清单上板联调。

## Windows 启动

准备 Python 3.12 和 uv。在 PowerShell 中执行以下命令。安装只在项目目录创建虚拟环境和本地模型目录，首次需要联网。

```powershell
Set-Location 'D:\Apostgraduate\opencode\embed-study\05-projects\desktop-robot'
.\setup-windows.ps1
```

安装结束后可以断网。启动程序时模型从本地文件加载，模型服务只监听本机回环地址，退出台架时一并停止。

```powershell
.\.venv\Scripts\python.exe -X utf8 robot.py --language zh
.\.venv\Scripts\python.exe -X utf8 robot.py --language en
```

按一次 Enter 模拟唤醒，听到提示音后说第一句。机器人播完会自动继续听，并保留最近四轮上下文。15 秒没有语音或说“结束对话”会结束当前会话。按 Ctrl+C 退出程序。说“前进”“后退”“左转”“右转”“停止”时，台架只在终端显示模拟动作。

默认用中文。改用英文时退出当前程序，再用 `--language en` 启动。中英文复用 SenseVoice 和 Qwen，分别用 MeloTTS 和 Piper Lessac 合成。每个进程只加载选中的音色。英文说 `End chat` 结束当前会话。`Move forward`、`Move backward`、`Turn left`、`Turn right`、`Stop moving` 只在整句匹配时显示模拟动作。

## 分别设置中英文音色

运行 `robot.py --list-voices` 列出音色。中文可选 `melo`、`zh-ll-0` 至 `zh-ll-4`、`theresa`，英文可选 `lessac`、`ryan`。编辑 `.local/voices.json` 里的 `zh` 和 `en` 可以分别保存默认值。安装脚本会在首次安装时复制 `voices.example.json`，已有设置会保留。改完重启程序生效。

```powershell
.\.venv\Scripts\python.exe -X utf8 robot.py --language zh --voice zh-ll-2 --preview-voice zh-ll-2.wav
.\.venv\Scripts\python.exe -X utf8 robot.py --language en --voice ryan
```

`--voice` 只覆盖当前启动的设置。加 `--preview-voice 文件.wav` 可生成一段试听，只加载所选的合成模型。

如果需要选麦克风或扬声器，先运行 `robot.py --devices`，再用 `--input-device 编号 --output-device 编号` 启动。台架以音量门限检测说话，在较安静的桌面测试。声音过轻时可降低 `--threshold`，持续被环境声触发时可提高门限。

## 复测

```powershell
.\.venv\Scripts\python.exe -m unittest -v
.\.venv\Scripts\python.exe -X utf8 bench.py
.\.venv\Scripts\python.exe -X utf8 bench.py --language en
```

`bench.py` 使用所选语言的合成音频走真实识别、生成和合成链路。每种语言 3 组各 5 轮，每组重新开始会话，回复音频分别放在 `.local/bench` 和 `.local/bench-en`。计时覆盖识别、生成及整段合成，实际麦克风模式另外输出从最后一个语音块到首句提交播放的估计值。

真人验收时，按 `bench.py` 中的 3 组问题逐句说。每组只按一次 Enter，最后说“结束对话”。逐轮记录识别是否准确、回复是否切题、播报是否听得清、等待几秒。第 1 阶段真人测试完成后，再按同一题组验证机载表现。

也可以用实际录制的 16 kHz 单声道 16 位 PCM WAV 复测。一次命令中的 WAV 顺序组成同一会话。

```powershell
.\.venv\Scripts\python.exe -X utf8 robot.py --wav '第一句.wav' '第二句.wav'
```

源代码默认只把录音和会话保存在运行内存中。文件测试生成的音频、下载模型和虚拟环境均在忽略目录，测试结束后可按需保留音频作为证据。
