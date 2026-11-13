# 框架验证记录

日期：2026-11-12。Windows、Python3.12.10，使用现有项目虚拟环境；这里只验证软件模型，不驱动硬件，不计学习日或学生能力过关。

| 检查 | 实际结果 | 能证明的范围 |
|---|---|---|
| 框架Python测试 | 33项通过 | 分帧/CRC/类型/范围、STOP编号去重、旧会话、token/帧/本地输入期限、重连和时钟故障、严格人声动作来源、差速数学 |
| 项目Python全套 | 174项通过，框架33项包含在内 | 与当前语音代码的导入/行为回归，不是174条真人语音或板端实测 |
| C前进联锁 | C17严格构建0诊断，8个场景通过 | 原forward_guard.c内核；不包含串口适配、真实控制任务、驱动和后退/转向 |
| 默认演示 | 最终DISARMED，从未DRIVING | 未显式开启时运动仿真禁用 |
| 视觉许可到期演示 | 心跳继续，新视觉缺失，200ms到BLOCKED | 主控心跳不续视觉许可；本地输入按演示显式刷新 |
| STOP演示 | 最终ARMED，active为空 | 停止可抢占，不需要新token；不是实际履带停车距离 |
| 重连演示 | 最终DISARMED，旧动作清空 | 不自动重放旧动作，需新握手前置和重新ARM |
| 独立审阅 | 发现的STOP编号复用、坏快照旧状态恢复、ToF状态不自动过期三项已修复并留回归 | 另核对了问句、null命令ID回执、帧/会话序号与时钟边界；不是安全认证 |
| 压缩包解压验证 | 隔离临时目录中33项通过、10行许可到期演示最终BLOCKED，ZIP CRC通过 | 只使用Python标准库运行框架，所有输出无硬件动作；不是全项目依赖安装或实物测试 |

四个演示输出始终`hardware_action=false`、`physical_verified=false`。原演示保留在`.local/framework-validation-20261112/`，最终演示在`.local/framework-validation-final-20261112/`；新会话nonce不复用回归随后加入，全套174/框架33项为最后代码版本结果。

## 实际执行命令

在桌面机器人项目目录：

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -p test_*.py
.\.venv\Scripts\python.exe -X utf8 -m unittest framework.test_wire framework.test_supervisor framework.test_motion_math
.\.venv\Scripts\python.exe -X utf8 -m compileall -q framework
gcc -std=c17 -Wall -Wextra -Wpedantic -Werror forward_guard.c test_forward_guard.c -o .local/framework-validation-20261112/test-forward-guard.exe
.\.local\framework-validation-20261112\test-forward-guard.exe
```

演示入口和场景命令见[主说明](README.md)。示例中的ms、mm/s和几何只用于验证逻辑，不是实车标定数据。语音服务本轮仍运行于香橙派；本目录未部署到板端、未开启串口、未拍摄/录音或发送真实动作。

## 实物未测清单

ESP32烧录与针脚、摄像头视场/材质误漏检、V4L2时钟语义、真实链路上界、屏幕色序与DMA时序、ToF采样截止、控制任务及看门狗最坏响应、编码器/PID/反转、履带扫掠和滑移、制动/滑行距离、电源压降/堵转电流、电池及充电、合盖散热和联合长测均为**未测**。

当前语音的独立结果见[自主维护记录](../autonomous-work-2026-11-12.md)：新唤醒候选和首段保护已部署，但真人准确率/完整质量/两秒声学目标未通过；短模型负载触发71.272°C实验停止，主动散热是后续硬件联调前置。
