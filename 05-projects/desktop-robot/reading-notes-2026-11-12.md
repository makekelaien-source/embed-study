# 语音机器人GitHub首轮源码阅读

2026-11-12。用户同意“小智→sherpa→Be More→小宸”的阅读次序，并追加Strata和Ollama。已完成所选文件的首轮只读核验，不代表通读全部仓库；保持暂停实验，未安装新软件、运行模型、新录音、修改板端或部署。

## 当前顺序与主要发现

| 顺序 | 对象 | 本轮已核到的要点 | 对当前项目的判断 |
|---|---|---|---|
| 1 | [小智后端](https://github.com/xinnan-tech/xiaozhi-esp32-server) | 音频接收、VAD/ASR、LLM、TTS与发送分层；存在回合标识与旧输出过滤。默认组件含在线LLM/TTS，具体provider决定是否真正边生成边出音频 | 优先借鉴接口、回合取消和回执组织；不直接照搬默认配置、无界队列或把发送结束当实物完成 |
| 2 | [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) | 小流式首遍持续给partial，端点后离线第二遍定稿；官方例子同步第二遍且阻塞采集 | 可以新增在线层、保留当前SenseVoice最终识别；partial只显示，不执行工具；两遍并不天然比单遍更快 |
| 3 | [Be More Agent](https://github.com/brenpoly/be-more-agent) | 语音、表情、相机的状态组织；ASR写死英语base.en，中文分句/文本过滤需改，相机调用rpicam-still | 借鉴整机交互，不能直接装上就成为中文A733机器人 |
| 4 | [小宸同学](https://github.com/HBConline/xiaochen-voice) | 简单规则与LLM分流，结果驱动确认；已读主路先获得完整文本、生成WAV，之后MQTT分片传输 | “流式传音频”不等于句内流式合成。Matcha与缓存值得登记候选，作者0.15秒注释不是本机实测，且会涉及声音变化 |
| 5 | [Strata](https://github.com/Niko1221/Strata) | 自有CPU/GPU混合MoE引擎，复用部分ggml内核；文字SSE接口与特定模型/显存主存管理 | 重点作为你的Windows RTX4080S＋64GB电脑端候选。官方ARM64 DGX Spark支持不等于A733可用；没有核到现成ASR/TTS接口 |
| 6 | [Ollama](https://github.com/ollama/ollama) | 模型常驻、runner调度、模板/参数、原生NDJSON流与分段耗时；加载参数变化可能触发重载 | 模型管理便利明确；现有llama-server已常驻，不能仅凭换Ollama承诺提速/提质。原生NDJSON与当前SSE客户端需适配 |

## Strata与Ollama分别读什么

Strata不是仅换一个界面或普通llama.cpp封装。阅读重点是其热专家GPU缓存、CPU缺失专家计算、CPU/GPU并行、内存预算、支持的模型架构和服务调用边界。已读硬件表包含Windows RTX40系列；对本项目而言，“用已有电脑承担更大模型”是可研究路线，必须明确它需要电脑开机和局域网，已经改变单板独立运行条件。本轮没有检查用户实际安装版本，也未推算4080S的真实首token速度。

Ollama重点是常驻与重载、上下文、模板、思考控制、采样和流式协议。原生`/api/chat`按行返回JSON，当前`LocalChat.reply_stream`按SSE的`data:`解析；不能只替换端口就认为兼容。若使用OpenAI兼容入口，也仍需逐项核验参数、思考控制、工具和结束原因的映射。`load_duration`、tokens/s、首个内容token、首个可播句和真实首声需要分别记录。

两者都不能自行补齐语音采集、Naruto检测、ASR、TTS或实际播放测量。使用更强模型可能改善回答能力，但具体权重、模板、历史与质量仍须各自验证，不能把运行时名称当准确率证明。

## 阅读中最有价值的三条接续线索

1. **先明确“流式”的层次。** 区分持续采集、在线识别、LLM文字流、句内音频生成、已生成WAV分片与边收边播。源码里叫stream或WebSocket双向通信，不等于整条链路已经全双工低延迟。
2. **把最终文本与实物结果作为提交边界。** partial可改写、旧回合输出可迟到；音量/移动只接受有效final一次。控制回复依据工具执行结果；未来履带还需实际驱动与停机证据，音频/网络发送结束不是硬件完成。
3. **分开研究单板与电脑端。** 单板优先比较语音前端、合成和调度；Strata/较大模型可作为电脑端路线研究。只搬走LLM仍保留端点、识别、合成和播放等待，是否能达到两秒不能仅看tokens/s。

这些是阅读后的候选方向，不是实验结论或迁移决定；当前生产仍保留原模型、音色、限频与服务配置。

## 分项阅读与证据范围

| 记录 | 已读范围 | 版本边界 |
|---|---|---|
| [xiaozhi.md](.local/reading-20261112/xiaozhi.md) | 服务端接收、VAD/ASR、LLM/TTS/发送及打断/工具/配置 | 固定commit `4b1a54a41c28112bc06b1ab605d2ba723f678ad3`；详见分项已读文件 |
| [sherpa.md](.local/reading-20261112/sherpa.md) | 两份官方麦克风endpoint/two-pass例子、模型页与当前robot.py | 读取当日master，未取得固定commit，不等于已验证本机2.0.1安装版行为 |
| [be-more.md](.local/reading-20261112/be-more.md) | README、agent.py、setup.sh | 当日main网页，未锁commit |
| [xiaochen.md](.local/reading-20261112/xiaochen.md) | tts/intent/voice_brain/mqtt_bridge/wakeword_server五文件 | 记录Git blob SHA，未锁原子整仓commit；不概括为完整设备层审计 |
| [strata.md](.local/reading-20261112/strata.md) | 架构/安装/模型文档、CMake条件、layer/expert/prefill与HTTP服务相关路径 | 当日main，未锁commit，未通读所有模型/后端 |
| [ollama.md](.local/reading-20261112/ollama.md) | 官方文档、sched.go/routes.go/api/types.go | 固定main commit `8a89b76cc7359805e48357ba7e5b99e845a4c211`，不混同release二进制 |

## 官方阅读入口

- [Strata原理](https://github.com/Niko1221/Strata/blob/main/docs/HOW_IT_WORKS.md)、[安装/硬件](https://github.com/Niko1221/Strata/blob/main/docs/INSTALL.md)、[HTTP服务源码](https://github.com/Niko1221/Strata/blob/main/serve/server.py)
- [Ollama Streaming](https://docs.ollama.com/api/streaming)、[常驻与配置FAQ](https://docs.ollama.com/faq)、[Linux ARM64](https://docs.ollama.com/linux)
- [sherpa双遍麦克风例子](https://github.com/k2-fsa/sherpa-onnx/blob/master/python-api-examples/two-pass-speech-recognition-from-microphone.py)
- [初始GitHub筛选与星数](github-voice-references-2026-11-12.md)

本轮属于教师项目研究，不计学生学习日、有效学时或能力过关。源码与阅读记录保留本地；既有Git目录写权限问题未解决，本轮未声称提交/推送成功。
