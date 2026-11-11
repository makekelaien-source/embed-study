# 香橙派 4 Pro 6GB 离线对话部署

板端目标为 **Orange Pi 4 Pro（A733）、Debian 12 Bookworm Server ARM64、Python 3.11**。中英文复用 SenseVoice INT8 和 Qwen3-1.7B Q4_K_M，默认中文用 MeloTTS、英文用 Piper Lessac，每次只加载所选音色。主机切换后需要分别实测 USB 音频、内存和延迟。第一阶段按 Enter 开始会话，后续再接 ESP32-S3 做语音唤醒。

## 1. 写系统卡与首次连接

电脑项目目录的 `.local` 已准备好 `Orangepi4pro_1.0.6_debian_bookworm_server_linux5.15.147.img` 和 `rufus-4.15p.exe`。镜像来自官方原文件镜像站，解压后已用压缩包内附的 SHA-256 核对。中文手册 §2.3（印刷页 11 起）演示了 balenaEtcher，要求 TF 卡至少 8GB、Class 10 或以上。套装的 32GB 卡容量足够，速度等级以实物为准。也可用已核对签名的 Rufus 对同一 `.img` 写盘，如询问模式则选 DD。写卡会覆盖目标盘，先按容量核对读卡器里的卡。Windows 如提示格式化，取消。 [镜像来源](https://appgobox.com/software/orange-pi-4-pro-official)

先贴好散热片，再在断电时插入写好的卡，接网线，最后上电。**4 Pro 的 USB-C 电源口只接受固定 5V，不进行 PD 协商。** 按中文手册 §2.1、§2.9（印刷页 8、33）使用 5V/3A 或 5V/4A 的适配器和可靠线材。首次上电先验证主板，SSH 和系统空间确认后再接 USB 麦克风和音箱。首次启动会自动扩容，期间保持供电。

- **接路由器。** 香橙派用网线接路由器，笔记本连同一路由器，查路由器的已连接设备列表。
- **网线直连 Windows 笔记本。** 如果笔记本 Wi-Fi 能联网，可在 `ncpa.cpl` 打开 Wi-Fi 属性的「共享」，将连接共享给与香橙派直连的「以太网」接口。共享会为这条链路提供 DHCP。上电后在 PowerShell 运行 `ipconfig` 查看该以太网口的地址，再用 `Get-NetNeighbor -AddressFamily IPv4` 查同一网段的板端地址，使用 `Test-NetConnection -ComputerName 板端IP -Port 22` 验证。 [Microsoft 的 ICS 说明](https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-wifi#allowinternetsharing)
- **已有 Linux 环境时可预设静态 IP。** 按中文手册 §3.7.5（印刷页 83–86），在首次启动前，从卡上 ext4 分区的 `/boot/orangepi_first_run.txt.template` 复制出 `orangepi_first_run.txt`。设置 `FR_net_change_defaults=1`、`FR_net_ethernet_enabled=1`、`FR_net_wifi_enabled=0`、`FR_net_use_static=1`，然后配置有线地址。例如板端用 `192.168.50.2/24`，笔记本有线端用 `192.168.50.1/24`，选与 Wi-Fi 不重叠的网段。配置文件只在烧卡后的首次启动生效，普通 Windows 文件管理器通常无法修改这张卡的 ext4 分区。 [厂商模板](https://github.com/orangepi-xunlong/orangepi-build/blob/next/external/packages/bsp/orangepi_first_run.txt.template)

中文手册 §3.8（印刷页 86–87）确认官方 Linux 镜像默认开启 SSH。指定镜像首次登录用 `orangepi` 账号和手册所列初始密码，随后运行 `passwd`。若找不到板，先区分网线链路、DHCP 地址和 TCP 22 是否可达，再考虑借 HDMI 显示器和 USB 键盘查启动状态。

## 2. 传部署包和安装

Windows PowerShell 中将第一行地址改成板端实际 IP。

```powershell
$board = 'orangepi@192.168.50.2'
ssh $board
```

登录后先确认型号、系统和空间。按手册 §3.6.1（印刷页 48–49），首次启动会自动扩展根分区。传包前确认根分区已接近卡的实际可用容量，且家目录所在文件系统有 **至少 6GB 可用空间**，同时容纳部署包、解压资产和编译目录。

```bash
uname -m
tr -d '\0' </proc/device-tree/model; echo
python3 --version
cat /etc/os-release
df -h / ~
free -h
```

通过上述检查后，另开一个 Windows PowerShell 窗口，将地址替换为实测值并传包。

```powershell
$board = 'orangepi@192.168.50.2'
scp 'D:\Apostgraduate\opencode\embed-study\05-projects\desktop-robot\.local\desktop-robot-orangepi4pro.tar' "${board}:~/"
```

指定镜像已检查包含 Python 3.11、编译器、make、PortAudio 与 ALSA 工具。模型、Python wheels、uv、CMake 和 llama.cpp 源码均已打包。只要能传文件，部署步骤可全程离线。

```bash
tar -xf ~/desktop-robot-orangepi4pro.tar -C ~
cd ~/desktop-robot
bash setup-orangepi.sh
```

脚本核对包内 SHA-256，离线安装 Python wheels，并编译同版本 `llama-server`。官方 b12119 ARM64 预编译包依赖 GLIBC 2.38，Debian 12 使用 2.36，因此板上从源码编译。若换了其他 Debian 12 镜像且缺少系统依赖，再联网安装 `build-essential libportaudio2 alsa-utils`。

## 3. 上板验收

```bash
cd ~/desktop-robot
.venv/bin/python robot.py --devices
.venv/bin/python robot.py --audio-check
set -o pipefail
.venv/bin/python bench.py 2>&1 | tee .local/bench-opi.log
.venv/bin/python bench.py --language en 2>&1 | tee .local/bench-opi-en.log
.venv/bin/python robot.py --language zh
```

- **录放音。** 先用 `arecord -l` 和 `aplay -l` 确认 USB 麦克风和 USB 音箱分别被识别。再用 `robot.py --devices` 找程序中的设备编号，在 `--audio-check` 与真人测试中都通过 `--input-device 编号 --output-device 编号` 选定同一对设备。清楚听到从目标音箱回放的三秒录音才算通过。手册 §3.13（印刷页 104–108）的声卡编号是板载或 HDMI 示例。
- **板上基准。** 运行同样的 3 组 15 轮合成音频，要求命令退出码为 0、15 轮均产出回复，日志在 `.local/bench-opi.log`。另开 SSH 用 `free -h` 观察内存和 swap。按手册 §3.14（印刷页 108–109）读取 `/sys/class/thermal/thermal_zone*/type` 和对应的 `temp`，温度原始值除以 1000 得到摄氏度。若 SSH 断开，先查供电、网线和系统日志。若模型报错，再看 `.local/llama.log`。
- **真人多轮。** 按 `bench.py` 的中、英文题组分别读，每组按一次 Enter。中文说“结束对话”，英文说 `End chat`。更换模式时退出当前程序，再以 `.venv/bin/python robot.py --language en` 或 `--language zh` 启动。每种语言分别统计切题、上下文和时延。项目目标仍为 12/15 条切题、6 条上下文追问至少答对 5 条，中位数 ≤5 秒、P90 ≤8 秒。程序的「说完到提交播放」是估计值，电脑合成音频的成绩单独保留。
- **断网。** 真人试聊可保留局域网 SSH 并切断上游互联网。若 Windows 直连靠共享分配地址，关闭共享可能同时断开 SSH。完全断开网络的验收可用下方命令延迟启动。30 秒内断开板子的网线和 Wi-Fi，给基准留足运行时间，再接回网线。核对日志起止的网卡状态、`bench_exit=0` 和 15 轮回复；若结束前就恢复了网络，重做这一项。完整的语音唤醒待 ESP32-S3 接入后复测。

```bash
nohup bash -c 'sleep 30; date -Is; ip -br addr; .venv/bin/python -u bench.py; result=$?; date -Is; ip -br addr; printf "bench_exit=%s\n" "$result"; exit "$result"' </dev/null >.local/bench-disconnected.log 2>&1 &
```

当前要等实板确认启动、音频兼容性、内存占用、温度和对话延迟。电源管理、电机驱动和壳体尺寸按 4 Pro 重新核对，待对话达标再定。

## 4. 分别设置中英文音色

编辑 `.local/voices.json` 的 `zh` 和 `en` 字段。中文可选 `melo`、`zh-ll-0` 至 `zh-ll-4`，英文可选 `lessac`、`ryan`。安装脚本会保留已有设置。改完重启对话生效。

```bash
.venv/bin/python robot.py --list-voices
.venv/bin/python robot.py --language zh --voice zh-ll-2 --preview-voice zh-ll-2.wav
.venv/bin/python robot.py --language en --voice ryan
```

`--voice` 仅覆盖当前启动，省略时用保存的设置。`--preview-voice` 只生成试听 WAV。实板延迟验收请使用最终选中的音色。
