# 开机自动语音与频率限制

## 当前配置（2026-11-12）

本机保留`desktop-robot-frequency.service`，并由其`conservative.conf`覆盖配置在启动后把A733大核policy6上限设为1716000kHz；内核调频和温度保护保持开启。源码中的`desktop-robot-conservative.conf`与已部署文件对应。不要在散热未解决时删除此限制或只安装基础频率恢复服务。

当前开机进入Naruto待机，使用SenseVoice主路及试验性多视图复核，唤醒后播放固定回应，进入原中英文模式；结束口令或15秒无有效输入后播放一次轻笑并回待机。唤醒准确率仍待真人复测，不等于稳定验收完成。收音/回退见[最新专项记录](autonomous-work-2026-11-12.md)。

新装系统部署开机服务时，同时安装基础单元与限频覆盖文件；以下针对当前A733板型、orangepi账号和固定目录，本机已在位，无需重装：

```bash
sudo install -Dm644 desktop-robot-frequency.service /etc/systemd/system/desktop-robot-frequency.service
sudo install -Dm644 desktop-robot-conservative.conf /etc/systemd/system/desktop-robot-frequency.service.d/conservative.conf
sudo install -Dm644 desktop-robot.service /etc/systemd/system/desktop-robot.service
sudo systemctl daemon-reload
sudo systemctl enable desktop-robot-frequency.service desktop-robot.service
sudo systemctl start desktop-robot.service
```

本文件下方为早期额定频率和无唤醒阶段的历史记录，不作为当前操作指令。最新实验发现短文本负载也会触发70°C实验停止条件，主动散热和高负载稳定性尚未通过。

> 本文为开机服务专项说明。第一阶段全部物料、操作、证据、未完成验收及其他MD索引见[阶段主文档](phase-1-offline-bilingual.md)。服务状态描述来自上次验证，当前是否在线需要重新上电检查。

## 历史部署记录（已由上方当前配置取代）

`desktop-robot-frequency.service` 在启动时把每个CPU频率策略的上限恢复到硬件公布的默认最高值：大核2002000kHz，小核1794000kHz。
没有超频，没有强制锁定performance调频，没有关闭内核温度保护；实际频率仍随负载和温度变化。
人工1716000kHz上限已解除，未来不要再运行旧 `.local/opi-thermal-cap.sh` 来设置它。

`desktop-robot.service` 自动寻找USB麦克风和音箱，恢复已验证的麦克风50%、音箱70%，加载模型并静默预热。
预热完成后播放一次短提示音，并向systemd报告`Offline voice ready`。空闲时不会每15秒重复提示音。
当前阶段提示音后可直接说话，不需要键盘；15秒无语音或说“结束对话”清除当前上下文，继续等待新一句。
当前没有ESP32唤醒词门槛；后续接入唤醒板后再改为唤醒待命。

本次正常重启验证：系统启动后约59秒就绪，其中服务加载约49秒。开机会自动开始加载，不代表零秒可用。
SD卡首次读取与后续热启动不同，不能用热缓存启动时间代替冷启动。

## 日常查看与切换

```bash
systemctl status desktop-robot.service
journalctl -u desktop-robot.service -f
cat ~/desktop-robot/.local/service-ready.json
sudo systemctl stop desktop-robot.service
sudo systemctl start desktop-robot.service
```

默认中文Theresa、速度0.9；英文Lessac、速度1.0。`fast-profile.json` 的`language_overrides`分别保存两种语言语速。
音色继续由 `.local/voices.json` 分别控制。
要让开机默认英文，在 `.local/robot-service.env` 写一行 `ROBOT_LANGUAGE=en`，再重启服务；改回中文写 `ROBOT_LANGUAGE=zh`。
设备匹配名称可通过同一文件里的`ROBOT_INPUT_NAME`与`ROBOT_OUTPUT_NAME`设置，不存账号密码。

手动跑录音检查、基准或其他模型服务前，先停止开机语音服务；测试完再启动，避免抢占麦克风和CPU。
如需彻底取消自启：`sudo systemctl disable --now desktop-robot.service`。频率恢复服务独立于语音服务，不会因停止聊天而重新限频。

新装系统复制源码后，可将两个`.service`文件安装到`/etc/systemd/system/`，执行daemon-reload、enable并start。
单元路径针对当前`orangepi`账号与`/home/orangepi/desktop-robot`，更换账号/目录须同步修改。

## 后续多模态融合

香橙派负责语音识别、对话、视觉理解与反馈协调；ESP32继续独立负责电机、桌沿传感器、心跳超时和急停。
先以轻量视觉模块识别人、物体或桌面状态，将短事件附到当前用户回合；现有Qwen是文本模型，需要视觉模块提供识别结果。
表情先绑定“听/想/说/空闲”等状态，或跟随播报音量变化；表情屏可交给ESP32绘制，避免传输逐帧大图。
视觉从低帧率与受限线程开始，采用独立进程和有界队列，只保留最新帧，语音和运动安全优先。
图像事件不要每帧重写系统提示词，以免损失当前提示词缓存。
持续运行大型视觉语言模型的速度、内存与散热尚未实测；加入摄像头、屏幕和底盘后必须重新验收联合负载与供电。
摄像头可辅助发现桌沿，实际防坠仍由ESP32直接读取桌沿传感器，不能等待聊天模型返回。

参考：[systemd服务就绪机制](https://github.com/systemd/systemd/blob/main/man/systemd.service.xml)、[OpenCV线程控制](https://docs.opencv.org/doc/doxygen/html/db/de0/group__core__utils.html)。
