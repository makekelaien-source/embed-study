# D22｜将文本命令接入事件队列与状态机

第一阶段 L6，连续 C。D21 已有多文件构建、头依赖故障修复、断言、事件序列与批量消费的真实测试。指针输出是在多轮局部提示后修订通过，编译/链接阶段曾混淆，仍需独立迁移。D22 在这个基础上增加文本命令到内部事件的适配和失败保持，使用已有函数，学生只写新增核心。G0 的统计、队列、解析、状态机全模块验收尚未通过，A02 的增量协议解析也尚未执行。板端、其他语言预算、30 小时周容量和 900 小时总量保留。

本教案是 300 分钟有效学习容量，休息另计，不能当作实际学时。当天按互动调整，行政备课和教师测试排除。

| 单元 | 分钟 | 新知识或深化目标与交付 |
|---|---:|---|
| D21 主动回忆 | 25 | 一个指针输出迁移和一个构建阶段判断，重点查实际薄弱点，记录提示程度 |
| 外部命令与内部事件的适配 | 40 | 完整讲清解析结果、事件枚举和提交结果三种含义，走通最小例，能说明何时修改队列 |
| 新增提交函数 | 65 | 学生实现 submit_command，复用 command_kind 与 queue_push；合法命令存入队尾，无效/满时保持 |
| 接入已有批量消费 | 50 | 教师准备依赖和构建，学生写新的测试入口，串起解析、提交、消费、状态检查，旧函数不重抄 |
| 失败路径诊断 | 45 | 自选一条能揭示先改队列再判命令错误的输入；在教师临时错误版找首次偏离并修复验证 |
| 集成验收与成本 | 45 | 正常、空命令、未知命令、满、回绕、双实例，检查状态与队列保持；说明解析及消费成本 |
| 复盘与 G0 差额 | 30 | 区分即时/提示/独立证据，列统计与增量协议待验项，给下一接口的输入输出契约 |

合计 300 分钟。每 45–60 分钟安排休息。提前通过时使用文末同主题扩展，保持一整块 C。

开场先问这一题，然后等待回答。`int received = -1; int *p = &received;`，函数形参是 `int *out` 时，调用实参应写 `p`、`*p` 还是 `&p`，出队成功后哪个整数对象得到新值？这是 D21 新知识回忆，不因学生看过示例就登记独立通过。后续第二个短检查给一个只含 `.o` 的 GCC 命令，让学生识别链接及所缺实现对象。

新知识首讲从一个业务情境开始。外部发来 `RUN`，解析器得到结果码 1；本设备内部对应的事件叫 `START`。结果码表示文字分类，事件枚举表示设备请求，二者按业务做明确映射。本题按原解析器仅支持大小写精确的 `RUN` 与 `STOP`。`RUNx`、空字符串和 NULL 都拒绝，不能让它们进入队列。后续文本行读取和更多命令另凭接口接入，本题不把它冒充二进制增量协议解析。

已有 command_kind 的返回契约如下。1 表示精确匹配 RUN，2 表示精确匹配 STOP，0 表示有字符串但未知，-1 表示 NULL。它只读输入，不修改队列和设备状态。输入为有效 NUL 结尾字符串或 NULL。讲解后先让学生预测 RUNx 的分类，再运行教师短例，之后发布新增核心。

新增接口计划为 `enum SubmitResult submit_command(struct IntQueue *q, const char *text);`，教师先在 `03-code_codex/D22-command-pipeline/submit-command.c` 创建空白文件，并给完整路径。已有文件保留原内容。头文件与旧依赖由教师准备，目标函数体由学生写。`enum SubmitResult { SUBMIT_OK, SUBMIT_INVALID, SUBMIT_FULL };`，数值按顺序为 0、1、2，调用方按名字比较。

| 提交结果 | 产生条件 | 可以依赖的结果 |
|---|---|---|
| SUBMIT_OK | 文本为 RUN/STOP，且事件成功入队 | RUN 映射 START，STOP 映射 STOP；只在队尾新增一项，旧项顺序保持，设备状态保持到消费阶段 |
| SUBMIT_INVALID | NULL、空字符串或未知字符串 | 队列所有字段和槽值保持，设备状态保持，无新事件 |
| SUBMIT_FULL | 文本合法，但队列已满 | 新事件未存入，旧队列及设备状态保持 |

q 指向合法、已初始化且只存合法设备事件的队列。text 有效期覆盖本次调用。本接口不处理事件，不修改设备状态，不分配动态存储。函数复用已验证 command_kind 和 queue_push，学生不用复制实现。题面给业务要求与验收，不给该目标函数实现。

最小业务带读从空队列、设备 IDLE 开始。提交 RUN 成功后队列保存 START，设备仍 IDLE；调用已有批量消费后，队列清空、设备 RUN。接着提交 STOP 并消费后设备 IDLE。队列已满时提交 RUN 返回 SUBMIT_FULL，旧队列与设备状态保持。这里“提交成功”和“设备已启动”分别由提交和消费两个阶段的证据判断。

验收至少包含空队列上分别提交 RUN/STOP；NULL、空串、RUNx 拒绝保持；满队列拒绝保持；取出一项再提交发生回绕；已有故障事件与 RUN 命令的顺序效果；两个队列及两台设备互不影响。提交成功而设备未改变的情况要留证，批量消费后再检查状态。教师运行批量边界，学生负责新增函数、测试入口设计与首个异常的诊断。

教师最小例是 `next-day-demo/D22-command-contract-check.c`。用严格 C11 选项链接已有共享解析器，检查 NULL、RUN、STOP、RUNx 与空串。它仅预检旧依赖契约，学生的新提交和集成函数尚未发生，不能登记通过。预检结果见同目录 D22-command-contract-validation.json。

同主题扩展使用剩余预算。让学生给相同最终状态但不同中间队列历史的两段命令，选择检查点揭示“非法命令误占一个槽”的错误。再检查 Make 中遗漏新适配头依赖的增量构建，先预测再实测，恢复正确依赖后按原验收重跑。核心都通过才讨论更高效的自动依赖生成，首次使用参数时完整讲清规则和最小例。扩展不追加每日容量。

G0 差额据实保留。这个学习日目标是解析分类、队列、状态机三者的适配与集成证据，统计模块仍须恢复旧代码核对接口并单独接入。无效状态与真正增量协议的全部错误恢复也须后续实际执行。不会以一次构建或一组教师测试宣称 G0/A01–A03 完成。D21 指针与构建诊断约 12 月 1–5 日安排延迟独立迁移，日复习与延迟复测分别记录。

授课依赖的已有定义列在后面。D22 实际发题同一条课堂正文也要贴出本题用到的完整定义，按最新文件核对，避免只给名字让学生猜接口。D21 日课源若已归档，应从学习册恢复到新的 D22 依赖目录，核对原字节，不能覆盖现有学生文件。

`03-code_codex/shared-command/d12-command-kind.h`

```c
#ifndef D12_COMMAND_KIND_H
#define D12_COMMAND_KIND_H
int command_kind(const char *command);
#endif
```

`03-code_codex/shared-command/d12-command-kind.c`

```c
#include <string.h>

int command_kind(const char *command){
    if (command == NULL)
    {
        return -1;
    }
    else if (strcmp(command,"STOP") == 0){
        return 2;
    }
    else if (strcmp(command,"RUN") == 0)
    {
        return 1;
    }else return 0;
}
```

`03-code_codex/D21-queue-device/D19-ring-queue.h`

```c
#ifndef D19_RING_QUEUE_H
#define D19_RING_QUEUE_H

enum { QUEUE_CAPACITY = 3 };
enum QueueResult { QUEUE_OK, QUEUE_FULL, QUEUE_EMPTY };

struct IntQueue {
    int slots[QUEUE_CAPACITY];
    unsigned int head;
    unsigned int tail;
    unsigned int count;
};

enum QueueResult queue_push(struct IntQueue *q, int value);
enum QueueResult queue_pop(struct IntQueue *q, int *out);

#endif
```

`03-code_codex/D21-queue-device/D19-ring-queue.c`

```c
#include "D19-ring-queue.h"

enum QueueResult queue_push(struct IntQueue *q, int value){
    if (q->count < QUEUE_CAPACITY)
    {
        q->slots[q->tail] = value;
        q->tail = (q->tail + 1) % 3 ;
        q->count ++ ;
        return QUEUE_OK;
    }
    return QUEUE_FULL ;
}

enum QueueResult queue_pop(struct IntQueue *q, int *out){
    if (q->count == 0)
    {
        return QUEUE_EMPTY;
    }else {
        *out = q->slots[q->head];
        q->head = (q->head + 1) % 3 ;
        q->count -- ;
        return QUEUE_OK;
    }
    
}
```

`03-code_codex/D21-queue-device/D20-device-state.h`

```c
#ifndef D20_DEVICE_STATE_H
#define D20_DEVICE_STATE_H
enum DeviceState { BOOT, IDLE, RUN, SAFE };
enum DeviceEvent { READY, START, STOP, FAULT, RESET };
enum DeviceState device_step(enum DeviceState current, enum DeviceEvent event);
#endif
```

`03-code_codex/D21-queue-device/D20-device-step.c`

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

`03-code_codex/D21-queue-device/consume-all.c`

```c
#include "queue-device-all.h"

enum QueueResult device_consume_all(struct IntQueue *q, enum DeviceState *state){
    int b = 1;
    int a = queue_pop(q,&b); int c = 0;
    while (a != QUEUE_EMPTY)
    {
        *state = device_step(*state, b);
        a = queue_pop(q,&b);
        c++;
    }
    if (c == 0 )
    {
        return QUEUE_EMPTY;
    }else return QUEUE_OK;
}
```
