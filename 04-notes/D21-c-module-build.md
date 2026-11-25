# D21｜把 C 模块构建成可运行的测试程序

当前是第一阶段 L6 的多文件、Make、断言与模块集成。D20 完成单链表本轮练习，状态机单步函数通过 20 格和连续路径教师测试。Make 已讲过单个目标文件的规则；头文件更新后的学生预测尚待回答。这个学习日继续用 C，先做可重复构建的程序，再将实际设备模块接入测试。G0 的统计、队列、解析和状态机整体验收另凭集成证据登记。板端、其他语言及实际学时照原计划保留。

## 开场问题

昨天的规则是 `device-step.o: D20-device-step.c D20-device-state.h`。若原先目标是最新的，现在只修改并保存 `D20-device-state.h` 中的事件枚举，再次调用 Make 时会发生什么？指出比较哪两个文件的修改时间即可。先等学生回答。顺带用一个短情境回忆 D20 的所有权：学生写下摘取堆节点前可保留哪个地址，以便摘取后释放它。

## 300 分钟安排

| 单元 | 分钟 | 交付与验收 |
|---|---:|---|
| D20 主动回忆 | 25 | 完成头文件问题及一次地址所有权迁移，记录实际需要的提示 |
| 从单个目标到可执行程序 | 45 | 读一张有两个对象文件和共享头的依赖图；分别预测源文件、头文件更新的影响，亲手构建并观察 |
| 断言与失败证据 | 45 | 解释边界 29/30，预测一条断言的结果；在教师临时副本引入单一可解释错误，读第一条失败位置，再恢复并复验 |
| 编写设备事件序列入口 | 65 | 复用已验证的 device_step，自写序列调用与返回处理，空序列、正常采集和故障恢复均通过；不重写四态规则 |
| 编译、链接与定位 | 55 | 为上述模块安排对象依赖，在教师准备的漏链接副本里识别出错阶段，补回缺失的对象后重新构建；记录前后结果 |
| 集成前的测试设计 | 40 | 选两条表面结果相近但中间路径不同的恢复序列；说明只查末态会漏掉哪种错误，并用原单步检查定位 |
| 复盘与下一集成接口 | 25 | 从 D19 队列与 D20 状态机中区分“保存事件”和“处理事件”的职责；给出空队列、入队失败以及成功消费时的调用预期，记录仍待验的 G0 项 |

各单元合计 300 分钟，休息另计。上表是容量，首次开课需采样并按实际互动分段，不把预检记为学生能力。

## 带读最小例

示例四个文件在 [D21-build](next-day-demo/D21-build/)。`sample.h` 声明 `int is_warm(int temperature);`，`sample.c` 的实现如下。

```c
#include "sample.h"

int is_warm(int temperature)
{
    return temperature >= 30;
}
```

`main.c` 调用它两次，温度是整数，30 含在阈值内。先比较输入 29，结果是 0；再比较 30，结果是 1。`assert(表达式)` 来自 `<assert.h>`，本例启用断言。条件为真时继续下一句，条件为假时给出失败位置并终止这次测试。把有副作用的操作单独执行后再检查，以免关闭断言时跳过本该执行的操作。

```c
#include "sample.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
    assert(is_warm(29) == 0);
    assert(is_warm(30) == 1);
    puts("SAMPLE_CHECKS=PASS");
    return 0;
}
```

从四个文件的临时副本所在目录执行 `mingw32-make`，它默认读取 `Makefile` 并构建第一条规则的目标。每条执行命令前是一个真正的 Tab。先从最终程序往回看依赖，再从缺失或过期的最底层目标开始执行。

```makefile
sample-check.exe: main.o sample.o
	gcc main.o sample.o -o sample-check.exe

main.o: main.c sample.h
	gcc -std=c11 -Wall -Wextra -Werror -pedantic -c main.c -o main.o

sample.o: sample.c sample.h
	gcc -std=c11 -Wall -Wextra -Werror -pedantic -c sample.c -o sample.o
```

首次先把两个源文件分别编译成对象，最后用对象链接成程序。在 PowerShell 运行 `.\sample-check.exe`，预期输出 `SAMPLE_CHECKS=PASS`。立即再构建会检查依赖并跳过已最新的目标。只更新 sample.c，应重新生成 sample.o 和可执行程序；两个 .c 都包含共享头，只更新 sample.h，应重新生成两个对象并重新链接。教师在同一工具链的临时副本已实测，四轮执行 gcc 的次数分别为 3、0、2、3；以上是教师预检。

## 学生新增核心

接口为 `enum DeviceState run_events(enum DeviceState initial, const enum DeviceEvent *events, size_t count);`。initial 为列出的合法状态；count 为元素数。零个事件时允许 events 为 NULL，返回初态。count 大于零时 events 指向至少 count 个合法事件。函数按原顺序把这些事件交给既有的 device_step，返回所有事件处理后的状态，原事件数组应保持原值。用本题新增函数复用原四态实现。

开课发题前，教师在 `03-code_codex` 准备 D21-run-events.c 空白文件和声明、测试入口，保留已有学生文件。将 D20 正式学习册中的下列头及实现按原字节恢复到新的 D21 依赖目录；用 `-I` 指向该目录，在同一条课堂正文贴出相关类型和既有函数定义。D20 独立文件归档清理后仍可从 [D20 学习册](../02-logs/D20-2026-11-25.md) 恢复。

已有类型与声明来自 D20-device-state.h：

```c
#ifndef D20_DEVICE_STATE_H
#define D20_DEVICE_STATE_H
enum DeviceState { BOOT, IDLE, RUN, SAFE };
enum DeviceEvent { READY, START, STOP, FAULT, RESET };
enum DeviceState device_step(enum DeviceState current, enum DeviceEvent event);
#endif
```

已有函数来自学生的 D20-device-step.c：

```c
#include "D20-device-state.h"
#include <stdio.h>
enum DeviceState device_step(enum DeviceState current, enum DeviceEvent event){
    if (current == SAFE && event == RESET)
    {
        return BOOT;
    }else if (current == BOOT && event == READY)
    {
        return IDLE;
    }else if (current == IDLE && event ==START)
    {
        return RUN ;
    }else if (current == RUN && event == STOP)
    {
        return IDLE ;
    }else if (event == FAULT)
    {
        return SAFE;
    }else return current; 
}
```

BOOT 为上电或故障复位后等待自检；IDLE 为自检通过或正常停止后的待机；RUN 表示已接受采集请求；SAFE 为报告故障后的锁定状态。READY 表示自检通过，START、STOP 是采集请求，FAULT 报告故障，RESET 请求清除故障。任意状态接受 FAULT，SAFE 经 RESET 回 BOOT，BOOT 经 READY 到 IDLE，IDLE 经 START 到 RUN，RUN 经 STOP 回 IDLE，其余组合保持。函数只返回状态，没有附加标志或样本输出。验收如下。

| 初态 | 事件序列 | 最终状态 |
|---|---|---|
| RUN | 零个事件 | RUN |
| BOOT | READY、START、STOP | IDLE |
| RUN | FAULT、RESET、START | BOOT |
| RUN | FAULT、RESET、READY、START | RUN |

## 同主题扩展与记录

提前通过时，用同一头文件和两个翻译单元演示漏列头依赖怎样产生旧对象，学生先预测增量构建与全量构建的差异，教师只在临时副本改变一处。恢复正确依赖后按原用例复验，保留失败输出。扩展使用本日剩余预算。D20 的即时理解与示范后修订另列，按实际学习日安排约 7±2 天后的独立迁移；D21 的作答、源码、有效学时与验收截至备课时均待发生。
