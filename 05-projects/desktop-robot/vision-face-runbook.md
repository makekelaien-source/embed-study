# 车头视觉与表情屏执行清单

> 后续底盘已改双履带，最新[视觉与显示规格](framework/vision_display.md)及[整机框架](framework/README.md)优先。下文保留早期双轮台架记录；不能将“两轮前方ROI”和前向许可直接当作履带后退、原地转向或全方向防坠覆盖。

摄像头接香橙派 4 Pro，从车头朝前下方看两轮将要驶过的桌面。ESP32-S3 负责 ToF、实体停机和电机，检查香橙派发来的前进许可。正面 IPS 彩屏接 ESP32-S3，仅呈现表情，素材可以替换为彩色 Q 版头像。

## 1. 备料和接线

| 物料 | 数量 | 检查内容 |
|---|---:|---|
| Linux UVC USB 摄像头 | 1 | 优先借一只现有摄像头。确认在实际安装距离能对焦、镜头能覆盖两轮前方、板上能连续采集。香橙派 4 Pro 手册 v1.4 §3.12.4 有 Linux USB 摄像头验证步骤。 |
| 可调俯角支架与 USB 数据线 | 各 1 | 安装后能锁定角度，保持两轮前方视野无遮挡，电机启动时镜头不晃。 |
| 微雪 2inch LCD Module，SKU 17344 | 1 | 非触摸 2 英寸 IPS，ST7789V 系列，240×320，四线 SPI。官方标称有效显示区 30.60×40.80 mm，载板外廓 58×35 mm。首版竖装，可放头像和肩部。 |
| 彩屏压框与 PH2.0 八芯线束 | 各 1 | 优先复用模块配套线。壳体开窗按有效显示区，固定点、插头和线束弯折空间按到手实物量。 |

[香橙派 4 Pro 手册](https://orangepi.net/wp-content/uploads/2026/01/OrangePi_4_Pro_A733_User-Manual_v1.4.pdf) · [彩屏型号与引脚](https://docs.waveshare.net/2inch_LCD_Module/) · [微雪商品页](https://www.waveshare.net/shop/2inch-LCD-Module.htm)

### 彩屏接线

| 屏端标记 | 连接 |
|---|---|
| VCC、GND | 稳压 3.3V 和共地。核对 ESP32 载板 3.3V 电源余量，测背光全亮时的电流与压降。 |
| DIN、CLK | ESP32-S3 通用硬件 SPI 的 MOSI 和 SCLK。LCD 仅写，无需 MISO。 |
| CS、DC、RST | 三个独立 GPIO，分别作低有效片选、命令/数据选择和低有效复位。 |
| BL | 用 ESP32-S3 GPIO 控制背光，按需做 PWM。SKU 17344 有板载背光开关，背光电流由 VCC 支路承担。 |

彩屏预留六个 GPIO。用实际开发板原理图安排引脚，核对启动绑带、Flash/PSRAM、USB、I²S、ToF 和电机引脚。ToF 走独立 I²C，彩屏走 SPI。接线按模块丝印核对两端针序。 [微雪模块原理图](https://files.waveshare.com/upload/e/ee/2inch_LCD_Module_SchDoc.pdf)

摄像头、麦克风、音箱和 ESP32 一起接入后再查设备列表和稳定性。Linux 用 `v4l2-ctl --list-devices` 找摄像头，优先用 `/dev/v4l/by-id/` 或 `/dev/v4l/by-path/` 下实际能采集图像的节点，并核对它支持的尺寸、像素格式和帧率。端口不足或供电压降过大时，再测试有独立供电且不会向主板反灌的 USB Hub。 [Linux V4L2 采集接口](https://docs.kernel.org/userspace-api/media/v4l/dev-capture.html)

## 2. 先用静止图像验证视觉

1. 车轮架空或电机断电。固定镜头，使画面上方对应较远的桌面，下方对应车前近处。用尺或临时标记测出两轮将经过的区域，并圈出能覆盖左右车轮和停车余量的 ROI。拆掉标记再采图。
2. 先在一张平整、低反光、有可辨纹理的桌面采一张完整且确定安全的参考图。相同镜头、角度、分辨率和光照下，采集完整桌面、桌沿进入 ROI、斜向桌沿、阴影、遮挡和模糊图。样本都标记真实位置。裸边低反差、近似地面纹理、反光或玻璃面必须单独验证，按实际结果决定是否允许在该桌面上移动。
3. 运行 `vision_check.py` 查看分类。它比较参考图与当前图中指定区域的桌面外观，并根据匹配情况输出 `CLEAR`（外观符合参考）、`EDGE`（疑似前方桌面结束）或 `UNKNOWN`（证据不足）。这是台架诊断，类别用于回放核对。普通单目图像的线条和颜色变化也可能来自桌纹或影子，视觉状态仍须与独立测距联锁。
4. 记录误停和漏检，先确认目标桌面上的直边和斜边均有足够提前量，再进入联动。镜头或桌面更换、外壳遮挡或安装角度变化后重做标定。

### 台架命令

Windows 在项目目录使用已有虚拟环境。安装 OpenCV 只用于视觉测试。

```powershell
uv pip install --python .\.venv\Scripts\python.exe opencv-python-headless==5.0.0.93
.\.venv\Scripts\python.exe vision_check.py --reference .local/reference.jpg --roi 80 100 480 320 --image .local/edge.jpg .local/occluded.jpg
```

香橙派可通过 SCP 复制 `vision_check.py` 和 `.local/vision-wheels/` 到对应目录。语音部署包继续用于第 1 阶段，视觉诊断单独安装。相机枚举与参考图采集需预先准备 Debian 的 `v4l-utils`、`fswebcam`。

```bash
.local/uv-aarch64-unknown-linux-gnu/uv --offline pip install --python .venv/bin/python --no-index --find-links .local/vision-wheels opencv-python-headless==5.0.0.93
v4l2-ctl --list-devices
camera=/dev/v4l/by-id/REPLACE_WITH_CAPTURE_NODE
v4l2-ctl -d "$camera" --list-formats-ext
fswebcam -d "$camera" -r 640x480 --skip 5 --no-banner .local/reference.jpg
.venv/bin/python vision_check.py --reference .local/reference.jpg --roi 80 100 480 320 --camera "$camera" --frames 20
```

替换摄像头节点和 ROI。这里的数字只示例 640×480 图像，实际区域按车轮和停车余量标定。相机采样会请求参考图尺寸，协商结果不一致则退出并报告 `UNKNOWN`。台架程序以样本数结束，实车连续采集还需要独立的读帧超时及许可管理。 [OpenCV 无界面版本](https://pypi.org/project/opencv-python-headless/5.0.0.93/)

## 3. 串口和前进联锁

| 条件 | ESP32 应执行 |
|---|---|
| 视觉连续给出新鲜许可、前部 ToF 有效且安全、串口健康、实体停机释放 | 只接受新的前进口令。每次仍限 300 毫秒，执行期间持续检查。 |
| 检出桌沿、画面不确定或前部 ToF 异常 | 拒绝新前进并中止当前前进，清除待执行动作。 |
| 相机掉线、旧帧、视觉进程卡住、串口中断或主控重启 | 默认禁止前进。ESP32 的本地许可到期后停轮，其他心跳不能续期。 |
| 条件恢复 | 先重新取得连续有效视觉结果，再等待新口令。 |
| 后退或转向 | 用该方向已实测的 ToF 覆盖及独立保护条件控制。未经验证的方向禁用。 |

香橙派的采集和分析与语音推理分开运行，保留最新帧并限制排队。摄像头结果带连接会话号、递增采集帧序号和剩余有效期。发出许可前按采集时间验证帧龄，扣除经测量的传输余量；ESP32 在本地用单调时钟计时。重复、乱序或旧会话的许可一律丢弃。发现危险时立即发撤销和停机，消息未送达时仍由本地许可超时和 ToF 执行保护。显示任务只读取状态。 [V4L2 帧序号和时间戳](https://docs.kernel.org/userspace-api/media/v4l/buffer.html)

从最危险的轮子到桌沿的实测提前量，要大于**最高测试速度 × 最坏响应时间 + 最差停车距离 + 余量**。最坏响应时间要算进采集、处理、串口和控制周期，也要覆盖许可超时才停的情况。停车距离分别测正常制动和断驱后滑行。先从约 3–5 cm/s 试跑，按结果设视觉许可时限和允许速度。对角接近桌沿时同样检查左右两轮，未达标时调整安装位置、降低速度或关闭对应动作。

### ESP32 联锁逻辑接入点

[前进联锁 C 模块](forward_guard.c)提供会话、视觉许可、动作受理和每次控制周期的驱动判定。上板时，在同一个控制任务内更新这些状态，用 ESP32 本地单调时间传入毫秒值。

- 握手确认新连接后调用 `forward_guard_begin_session`。串口层核对当前启动与握手标识，给模块分配递增的本机会话号，拒绝重启前或前一连接缓存的消息。
- 把经采集时间、连续帧和标定检查的结果交给 `forward_guard_receive_vision`。每帧只发送一次，编号递增。遇到无新帧的故障也立即发停止事件。`200 ms` 是软件许可上限，实车时限按最坏响应和停车距离验证后取更严值。
- 收到新前进口令时调用 `forward_guard_start`。每个控制周期和收到视觉结果、重连、停止事件后立即调用 `forward_guard_poll`。输入前 ToF、心跳和实体停机的综合结果；显式停止时传入假。返回假时，驱动适配层立即停止前进。串口层须限制命令队列和时效，并在保护触发或重连时清空积压动作。

在项目目录可独立编译和测试这段逻辑。

```powershell
gcc -std=c17 -Wall -Wextra -Wpedantic -Werror forward_guard.c test_forward_guard.c -o .local/test-forward-guard.exe
.\.local\test-forward-guard.exe
```

## 4. 表情屏素材与固件

| 状态 | 画面 |
|---|---|
| 待机 `idle` | 放松的眼睛和浅笑 |
| 听取 `listening` | 睁圆眼睛，嘴闭合 |
| 处理 `thinking` | 眼睛偏向一侧 |
| 播报 `speaking` | 张嘴，固件可按播报状态切换嘴形 |
| 停机 `blocked` | 警觉表情，优先于正在播报等对话状态 |

在电脑上用 `face_screen.py` 导出 240×320 彩色预览和 RGB565 素材。内置五个表情供台架用。之后为同一个角色准备各状态 PNG，导入时保留宽高比并居中，透明区域合成到背景。每种状态用独立文件命名，运行时由 ESP32 选择当前表情。

```powershell
uv pip install --python .\.venv\Scripts\python.exe Pillow==13.0.0
.\.venv\Scripts\python.exe face_screen.py blocked .local/blocked.png
.\.venv\Scripts\python.exe face_screen.py blocked .local/blocked.rgb565
.\.venv\Scripts\python.exe face_screen.py idle .local/chibi-idle.rgb565 --artwork .local/chibi-idle.png
```

最后一条命令使用自备角色 PNG。`.png` 用于电脑预览。`.rgb565` 无文件头，像素按行从左到右、从上到下排列，每像素两字节，高字节在前，整帧 153,600 字节。

1. 在 ESP-IDF 用 SPI LCD 驱动初始化 ST7789。先显示已生成的 `.local/st7789-face-assets/panel-check.rgb565` 测试图，用红、绿、蓝和四角标记确认通道顺序、字节序、竖屏方向和边界。将素材按行分块送屏，并等 DMA 传输完成后再复用对应缓冲。
2. 首版在表情状态变化时刷新。之后做眨眼或口型时优先局部更新，用小块 DMA 缓冲和有限队列。五张未压缩全帧素材约占 750 KiB，固件打包时核对应用分区与 ESP-SR 模型分区余量。
3. 表情任务低优先级，只读最新状态。显示链路堵塞时跳过后续刷新，由显示任务单独处理恢复。安全任务独立采样与停机。架空比较空闲、持续刷新、屏幕断开和刷新超时下的停机时序。

[ESP-IDF SPI LCD 驱动](https://docs.espressif.com/projects/esp-idf/en/v5.5.6/esp32s3/api-reference/peripherals/lcd/spi_lcd.html)

## 5. 验收顺序

| 顺序 | 操作与通过条件 |
|---|---|
| 1. 静态回放 | 用已标记的实拍图核对参考匹配、桌沿和不确定分类。记录光照、材质、距边距离、误报与漏检。 |
| 2. 架空联锁 | 发送前进期间复现桌沿、拔摄像头、遮镜头、卡住视觉进程、回放旧帧、拔串口和重启。验证无自行恢复前进。屏幕超时和断开不改变停机时序。 |
| 3. 围挡与系绳 | 先在地面围挡内低速试跑，再系防坠绳验证直向、左右斜向和桌角。用慢速录像核对最先靠近边缘的承重轮及余量。 |
| 4. 满负载 | 同时开启摄像头、推理、播报和彩屏全亮刷新，量采集到停轮的最坏时间、供电压降和对话延迟，再核定速度与许可时限。 |
| 5. 合盖复测 | 固定镜头和彩屏，重查镜头及 ToF 视野，复测桌沿、异常停机、状态表情和充电。 |

当前可在电脑上验证图像诊断、前进联锁核心、彩色表情预览和素材导出。连续采集服务、屏幕与电机驱动、实物接线、视野、停车距离和合盖结果均待在对应阶段联调实测。
