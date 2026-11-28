# D23｜统计接入设备，完成 PC 模块联动

第一阶段 L6，继续连续 C。D22 已完成命令提交、启停和双设备隔离的实际验证，多处是按反馈修订通过。统计接入题 collect_samples 仍为空，学生收课时明确最近的测试没有做，D23 从这里续写。教师统计辅助函数检查与学生本题完成分别留证。

G0 的统计、队列、解析、状态机完整联动尚未验收。真实增量协议解析尚未授课和执行，A02 仍待后续安排。板端和其他语言余额、周 30 小时、总 900 小时保留。下面 300 分钟是计划容量，实际时长按采时登记，休息和教师处理另计。

**当周目标与进度**

L6 包括多文件、Make、断言、链表和模块集成。已有多文件构建与头依赖修复证据，链表为提示后完成，命令、队列和状态机已接通。当前待完成统计接入、四模块联合测试、独立诊断与延迟迁移。真实前置缺口局部补强，内容进度和实际学时分开。

| 单元 | 分钟 | 新增或深化目标 | 交付 |
|---|---:|---|---|
| D22 主动回忆 | 25 | 提交与消费时刻、断言副作用、结果有效性 | 一道短诊断及提示记录 |
| 完成统计状态控制 | 55 | 结构体输出指针，区分保留旧结果与生成本批空结果 | 学生 collect_samples 及原测试 |
| 四模块联动 | 70 | 命令、队列、设备状态与采样结果的执行顺序 | 新测试入口和分阶段断言 |
| 结果有效性与故障诊断 | 45 | 未运行、全无效、空批和真实零均值的区别 | 区分用例、首次错误写入与修复复验 |
| 构建与成本深化 | 60 | 跨目录头依赖、多批数据工作量 | 构建证据与 e/n 两种规模解释 |
| 复盘与 G0 差额 | 45 | 已完成、提示完成、未测和接口契约 | 联合验收表及下一接口说明 |

合计 300 分钟。每 45–60 分钟短休息，70 分钟段分成两段，中间休息另计。提前完成用文末同主题扩展。首段若出现指针写回卡点，用一个局部结构体赋值例补强，再回原题。

**开场只问这一题**

报告里 valid_count 为 0，average 为 0。可以把它解释成“测得 0 度”吗？先看哪个字段？

先等回答。D22 有即时正确回答，本次能解释就进入代码，避免同义复问。随后用一个短诊断回忆为何操作调用应先执行、再用 assert 检查返回值。D22 的 NDEBUG 示例实际输出从 1 变 0，按既有证据带读。

**接续空白核心**

文件为 D:/Apostgraduate/opencode/embed-study/03-code_codex/D22-statistics/collect-samples.c。开课核对内容，已有学生代码就续用。包含 collect-samples.h，学生实现接口 enum CollectResult collect_samples(enum DeviceState state, const int samples[], int count, struct SampleStats *out)。

state 为当前设备状态，samples/count 为本批数组及数量，out 指向调用者结果对象。out 有效，count 非负，数组至少有 count 项，累加不超出 int。count 为 0 时 samples 可为 NULL。输入数组只读，state 使用已定义四态。

| 返回值 | 数值 | 条件 | 调用后结果 |
|---|---:|---|---|
| COLLECT_OK | 0 | RUN 且统计后 valid_count 大于 0 | out 四字段为本批结果，average 可作为有效均值 |
| COLLECT_NO_DATA | 1 | RUN 且本批没有有效数据 | out 为本批统计，average 为占位 0，invalid_count 区分空批与全无效 |
| COLLECT_INACTIVE | 2 | BOOT、IDLE、SAFE | out 原有全部字段保留，本次未更新报告 |

复用 summarize_samples。它返回完整 SampleStats，普通结构体赋值复制字段值，写回 out 指向对象后调用者才能看到新报告。本题函数实现留给学生。

最小例 {20,-999,30} 在 RUN 下得到 2/1/50/25 和 COLLECT_OK。SAFE 下相同样本返回 COLLECT_INACTIVE，原报告保持。RUN 下 {-999,-999} 生成 0/2/0/0 并返回 COLLECT_NO_DATA，覆盖旧报告。空批生成 0/0/0/0。真实样本 {0} 生成 1/0/0/0 并返回 COLLECT_OK。

test-collect.c 已准备三种非运行状态保持、正常统计、输入保持、运行后故障保持、全无效与空批。教师严格 C11 构建执行学生代码，保留首稿和失败，修复后重跑原验收。当前核心未写，整体验收未执行。

**四模块联动练习**

collect_samples 完成后，教师在 03-code_codex/D23-device-statistics/ 创建空白 test-main.c，并在发题正文给完整路径。准备引用已有模块和构建入口，学生只写新增入口。实际发题同一正文贴出所调用旧函数的完整定义和类型。

| 时刻 | 设备状态 | 统计要求 |
|---|---|---|
| 初始 IDLE 时采样 | IDLE | COLLECT_INACTIVE，旧报告保持 |
| 提交 RUN，尚未消费，采样 | IDLE | 旧报告保持 |
| 消费启动事件后采样 | RUN | COLLECT_OK，本批结果 |
| RUN 下采全无效批 | RUN | COLLECT_NO_DATA，本批空结果覆盖旧结果 |
| 提交 STOP，尚未消费，采样 | RUN | 仍可统计 |
| 消费停止事件后采样 | IDLE | COLLECT_INACTIVE，保留停止前报告 |

操作先执行再检查返回值，逐步检查状态、队列和报告。教师补测空串、未知命令、满、回绕和双实例。学生选择最终状态相同、中途报告不同的路径检查执行顺序。需要 FAULT、RESET、READY 时用已有 queue_push 加入内部事件，当前文本解析器仅接 RUN/STOP。

**错误定位**

教师在临时副本植入“非运行状态也覆盖 out”的错误。学生选择旧报告、状态和新批次，先列应保持的字段，再定位首次错误写入，修正后按相同验收复跑。结合真零均值、全无效、空批、设备未运行，解释为什么相同数值可能有不同业务含义。这段练习结果契约和错误定位，不要求重写已有统计循环。

**构建与成本**

先读现有 Makefile 的跨目录源和头依赖。新统计头同时被两个对象包含，修改定义后应重编两份对象并链接。教师准备临时副本，学生预测执行哪些规则，再实测。NDEBUG 深化时先说明纯断言使用的变量可能触发未使用警告，保持严格编译要求，按程序用途处理诊断。

事件数记为 e，样本数记为 n。单步环形出队 O(1)，消费 e 项 O(e)，统计 n 项 O(n)，每批先消费再统计合计 O(e+n)。统计只使用一个结果结构体，额外空间 O(1)，输入数组和已有队列存储另计。要求用实际遍历和函数调用次数解释。

**同主题扩展**

两设备各自保存统计报告，一台 SAFE 保持旧报告，另一台 RUN 刷新，检查隔离。再设计有效数量不同但平均值相同的两批数据，说明只比较 average 会漏掉哪个错误。新增接口先讲规则与最小例，核心由学生写，扩展替换剩余容量。

**收口与复测**

D22 的输出指针、字符串与枚举、函数调用、返回枚举和断言副作用约 12 月 3–7 日安排精简延迟迁移。D23 新增结构体写回和结果契约在实际学习日后 5–9 天安排，开课采时后填写日期。日复习与延迟复测分别留证。

G0 按统计、解析、队列、状态机联合路径逐项记录。教师短例通过只记教师预检，学生实现、独立解释、错误修复与延迟迁移分别登记。增量协议和板端的未验项继续保留。

**教师预检**

时间 2026-11-28T18:53:20+08:00。实际以 gcc -std=c11 -Wall -Wextra -Werror -pedantic 编译 teacher-stats-check.c 与 sample-stats.c 到系统临时目录。编译退出 0，运行退出 0，输出 D22_STATS_CHECKS=PASS。七组覆盖原样本、普通混合、全无效、空批、负数单项、非整数平均及真实零值，并检查输入保持。collect_samples 核心仍空，其整体功能尚未运行。

统计实现 SHA-256 为 9ac5b972a80302ba308120a95921c6eede6d2917e14ca7a5be4f72d92c859ad2，测试源 SHA-256 为 29f31ff12179b47f0828f29b156bc7891815f94d25324000dbd3cdf91b2a06fa。

**已有定义原文**

实际发题前核对最新版本，在同一课堂正文贴出相关定义。

来源 [03-code_codex/D22-statistics/sample-stats.h](../03-code_codex/D22-statistics/sample-stats.h)

```c
#ifndef D22_SAMPLE_STATS_H
#define D22_SAMPLE_STATS_H
struct SampleStats {
    int valid_count;
    int invalid_count;
    int sum;
    float average;
};
struct SampleStats summarize_samples(const int samples[], int count);
#endif
```

来源 [03-code_codex/D22-statistics/sample-stats.c](../03-code_codex/D22-statistics/sample-stats.c)

```c
#include "sample-stats.h"

/* Teacher extraction from D2 reference-d2-statistics.c.
   Reuses the student's fault rule and accumulation; returns fields to caller. */
int is_fault(int value)
{
    if (value == -999)
    {
        return 1;
    }else return 0;
}

struct SampleStats summarize_samples(const int samples[], int count)
{
    struct SampleStats result = {0};
    for (int i = 0; i < count; i++)
    {
        if (is_fault(samples[i]) == 1)
        {
            result.invalid_count++;
        }else {
            result.sum += samples[i];
            result.valid_count++;
            result.average = (float) result.sum / result.valid_count;
        }
    }
    return result;
}
```

来源 [03-code_codex/D22-statistics/collect-samples.h](../03-code_codex/D22-statistics/collect-samples.h)

```c
#ifndef D22_COLLECT_SAMPLES_H
#define D22_COLLECT_SAMPLES_H
#include "sample-stats.h"
#include "../D21-queue-device/D20-device-state.h"
enum CollectResult { COLLECT_OK, COLLECT_NO_DATA, COLLECT_INACTIVE };
enum CollectResult collect_samples(enum DeviceState state,
                                   const int samples[], int count,
                                   struct SampleStats *out);
#endif
```

来源 [03-code_codex/D22-command-pipeline/submit-command.h](../03-code_codex/D22-command-pipeline/submit-command.h)

```c
#ifndef D22_SUBMIT_COMMAND_H
#define D22_SUBMIT_COMMAND_H

#include "../shared-command/d12-command-kind.h"
#include "../D21-queue-device/D19-ring-queue.h"
#include "../D21-queue-device/D20-device-state.h"

enum SubmitResult { SUBMIT_OK, SUBMIT_INVALID, SUBMIT_FULL };
enum SubmitResult submit_command(struct IntQueue *q, const char *text);

#endif
```

来源 [03-code_codex/D22-command-pipeline/submit-command.c](../03-code_codex/D22-command-pipeline/submit-command.c)

```c
#include "submit-command.h"

enum SubmitResult submit_command(struct IntQueue *q, const char *text){
    int a = command_kind(text);
    if (a == -1 || a == 0)
    {
        return SUBMIT_INVALID;
    }else{
        if (q ->count == QUEUE_CAPACITY)
        {
            return SUBMIT_FULL;
        }else if (a == 1)
        {
            queue_push(q,START);
        }else if (a ==2)
        {
            queue_push(q,STOP);
        }
        return SUBMIT_OK;
    }
    
}
```

来源 [03-code_codex/shared-command/d12-command-kind.c](../03-code_codex/shared-command/d12-command-kind.c)

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

来源 [03-code_codex/D21-queue-device/D19-ring-queue.h](../03-code_codex/D21-queue-device/D19-ring-queue.h)

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

来源 [03-code_codex/D21-queue-device/D19-ring-queue.c](../03-code_codex/D21-queue-device/D19-ring-queue.c)

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

来源 [03-code_codex/D21-queue-device/D20-device-state.h](../03-code_codex/D21-queue-device/D20-device-state.h)

```c
#ifndef D20_DEVICE_STATE_H
#define D20_DEVICE_STATE_H
enum DeviceState { BOOT, IDLE, RUN, SAFE };
enum DeviceEvent { READY, START, STOP, FAULT, RESET };
enum DeviceState device_step(enum DeviceState current, enum DeviceEvent event);
#endif
```

来源 [03-code_codex/D21-queue-device/D20-device-step.c](../03-code_codex/D21-queue-device/D20-device-step.c)

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

来源 [03-code_codex/D21-queue-device/queue-device-all.h](../03-code_codex/D21-queue-device/queue-device-all.h)

```c
#ifndef D21_QUEUE_DEVICE_ALL_H
#define D21_QUEUE_DEVICE_ALL_H

#include "D19-ring-queue.h"
#include "D20-device-state.h"

enum QueueResult device_consume_all(struct IntQueue *q,
                                    enum DeviceState *state);

#endif
```

来源 [03-code_codex/D21-queue-device/consume-all.c](../03-code_codex/D21-queue-device/consume-all.c)

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

