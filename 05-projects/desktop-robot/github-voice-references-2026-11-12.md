# 树莓派与香橙派语音对话：GitHub参考筛选

检索日期：2026-11-12。用户最新决定先暂停新增实验，先找GitHub高星参考；本轮不安装、不换模型、不修改板端服务。Stars来自当日GitHub REST API快照，会变化；原始元数据及部分README在`.local/github-reference-20261112/`。项目自身宣传的实时、低延迟或秒级不是本机测试结果。

这里把语音识别ASR、语言模型LLM、语音合成TTS和完整对话系统分别判断。目标硬件为现有Orange Pi 4 Pro A733 6GB；树莓派或其他香橙派的CPU/NPU/GPU成绩不能直接移用。

## 1. 优先参考

| 仓库 | Stars快照 | 类别 | 值得阅读什么 | 本项目适配边界 |
|---|---:|---|---|---|
| [xinnan-tech/xiaozhi-esp32-server](https://github.com/xinnan-tech/xiaozhi-esp32-server) | 11,264 | 完整中文语音后端 | VAD/ASR/LLM/TTS模块划分、会话/工具/设备协议、流式服务组织、Ollama与本地ASR适配 | 当前官方部署文档有amd64/arm64镜像。默认服务选择含在线TTS等，不能把“服务器部署在本地”当全链路离线；本地模型资源另算 |
| [brenpoly/be-more-agent](https://github.com/brenpoly/be-more-agent) | 1,150 | 树莓派完整机器人 | OpenWakeWord→Whisper.cpp→Ollama→Piper及Idle/Listening/Thinking/Speaking表情、相机扩展 | README建议Pi5或至少4GB的Pi4；源码默认base.en/英文识别与英文Piper，分句及文本过滤也需改才能支持纯中文；rpicam相机不是A733通用接口。适合借鉴组织，不是中文开箱成品；DuckDuckGo搜索需网络 |
| [k2-fsa/sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) | 15,898 | 语音底座 | 中英流式ASR、小流式首遍＋离线第二遍、VAD/KWS/语音增强与TTS | 当前SenseVoice/Theresa已在这个生态；值得比较具体模型与数据流，而不是把同一框架重新安装当提速。普通ASR不等于Naruto定制唤醒 |
| [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp) | 55,123 | 语音识别 | Pi/CPU/量化路径、麦克风与命令示例、talk-llama完整链路示例 | 不是语言模型本身；stream示例是周期滑窗转写。中文要选多语版，不能照搬.en模型；talk-llama README的M2 Ultra演示不代表Pi/A733性能 |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | 134,205 | LLM推理底座 | GGUF量化、ARM构建、服务器/缓存/线程与llama-bench对照 | 本项目已经使用。另换封装不自动提高同一模型知识正确率，也不能把树莓派5的A76或其他GPU成绩当A733成绩 |
| [ollama/ollama](https://github.com/ollama/ollama) | 186,743 | LLM运行与管理 | ARM64部署、模型管理、API与常驻策略；大量整机参考使用它 | 便于编排和接入，不是独立ASR/TTS，也不意味着比当前llama.cpp更快；模型可能运行在本机或另一台局域网主机，需要看实际地址 |
| [Niko1221/Strata](https://github.com/Niko1221/Strata) | 约43.3k（网页） | CPU/GPU混合MoE引擎与服务 | 用户之前使用的仓库；专家缓存/分工、特定模型与内存、文字API和平台边界 | 官方Windows RTX40系列与用户电脑接近；ARM64 DGX Spark不代表A733。先研究电脑端价值，不当现有6GB板的直接替代 |
| [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl) | 6,260 | 本地TTS | 持续维护的Piper实现、Python/C++接口和音频输出组织 | 与首声等待直接相关；更换引擎/声音需分别验证中文、音色和首段耗时，不能从英文或桌面演示推算Theresa收益 |
| [microsoft/BitNet](https://github.com/microsoft/BitNet) | 41,547 | 特殊低比特LLM路线 | ARM低比特内核、原生BitNet模型、CPU部署方式 | 不是把现有Qwen GGUF直接改成1bit；官方2B4T卡说明非英语支持有限。只列备用研究路线，不作为当前中英默认替换 |

上表千星的Be More Agent按完整机器人相关性保留；其余为数千至十几万星底座/后端。Stars表示关注度，不证明当前中文质量或两秒端到端目标。

## 2. 与硬件特别贴近、但不能称高星的实例

| 仓库 | Stars快照 | 为什么保留 | 需核实什么 |
|---|---:|---|---|
| [HBConline/xiaochen-voice](https://github.com/HBConline/xiaochen-voice) | 43 | README明确香橙派4 Pro、ESP32-S3、SenseVoice、Qwen3-0.6B、Matcha、ST7789；与当前后续路线相近 | README的板卡/系统与具体性能仍属作者描述，未复现实板。其快速唤醒提示、规则直达指令与通用问答是不同路径，不能把前两者速度当知识问答首声 |
| [PiSugar/whisplay-ai-chatbot](https://github.com/PiSugar/whisplay-ai-chatbot) | 534 | Pi便携聊天设备，包含屏幕、音频、供电及预制镜像，README建议Pi5 8GB用于离线版 | PiZero2W也在标题中，但不能据此认为全套LLM适合512MB独立运行；选择的provider决定是否真正离线，HAT驱动不是A733通用驱动 |

当前主板是A733，不直接套用RK3588/RKNN教程；香橙派不是单一芯片平台。语音NPU/GPU部署需核验芯片、驱动、模型格式与算子支持。

## 3. 用户确认的精读顺序（加入Strata、Ollama）

2026-11-12用户接受上轮回复中的“小智→sherpa→Be More→小宸”顺序，并要求加入Strata与Ollama。保持原四项次序，在其后分别阅读两个运行时；Whisplay、llama.cpp/Piper、BitNet保留为对应模块的补充资料。此处替换初始建议次序，不恢复实验。

| 顺序 | 阅读对象 | 固定输出 |
|---|---|---|
| 1 | 小智后端 | 音频到回答的真实调用链、队列/打断、工具回执、本地/在线provider边界 |
| 2 | sherpa-onnx | 中英流式首遍/离线复核的数据流，partial/final、endpoint与流重置，现有代码最小差异 |
| 3 | Be More Agent | 语音/表情/相机状态编排；默认英文、中文分句和树莓派接口的适配项 |
| 4 | 小宸同学 | 相近香橙派方案的规则快路、LLM调用、合成与MQTT音频分片；核对“流式”具体发生在哪一层 |
| 5 | [Strata（Niko1221/Strata）](https://github.com/Niko1221/Strata) | 用户原来使用的仓库；模型/原生引擎、CPU/GPU分工与内存、API、平台要求；区分A733板端与4080 Super电脑端的价值 |
| 6 | Ollama | 模型常驻、streaming、上下文与思考/采样、运行后端和ARM64；与现有llama.cpp比较，区分管理便利和已证明的性能收益 |

每项保留已读文件/版本、可借用模块、依赖与不适用项、对准确率/回答质量/首声的影响及证据缺口。源码阅读记录统一见[reading-notes-2026-11-12.md](reading-notes-2026-11-12.md)，不把阅读当实现、实验或实板验收。

## 4. 核验入口

- [小智当前部署说明](https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/Deployment.md)：本次原始文件明确同时提供amd64和arm64镜像；历史fork中“仅x86”描述不能替代当前主仓库。
- [sherpa小流式与两遍识别](https://k2-fsa.github.io/sherpa/onnx/pretrained_models/small-online-models.html)：官方给出小流式模型作第一遍、非流式模型作第二遍的建议，列出中英双语候选。
- [whisper.cpp的talk-llama](https://github.com/ggml-org/whisper.cpp/blob/master/examples/talk-llama/README.md)：语音与LLM及会话缓存的集成示例；性能演示硬件不是本项目板卡。
- [Be More Agent源码](https://github.com/brenpoly/be-more-agent/blob/main/agent.py)及[安装脚本](https://github.com/brenpoly/be-more-agent/blob/main/setup.sh)：核验默认英文与Pi相机依赖，安装脚本也不能替代逐项核对Whisper编译和权重准备。
- [Ollama Linux ARM64说明](https://docs.ollama.com/linux)：确认运行架构，不能据此认定A733 NPU加速。
- [BitNet官方模型卡](https://huggingface.co/microsoft/bitnet-b1.58-2B-4T)：模型适用范围与专用内核要求。
- [Home Assistant的Ollama集成](https://www.home-assistant.io/integrations/ollama/)：可额外研究“语音终端—会话代理—局域网LLM”结构，不必把完整智能家居平台装进当前桌面机器人。

## 5. 当前接续与暂停边界

本次仅完成资料筛选。用户提出暂停前，少量电脑离线诊断已保留在`.local/breakthrough-20261112/`；新质量对照仅完成1条后停止，自有llama-server已退出，不能将不完整结果概括成质量结论。没有新增真人录音、板端负载、安装或生产部署。

下一步先逐文件阅读前述项目，整理“可借用模块—依赖—本地/远端—当前代码差异”；未经新指令不恢复新增实验。准确率、知识质量和说完到有效声学首声两秒仍是分别待验收目标。
