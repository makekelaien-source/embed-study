# D20｜状态机、节点地址和构建规则复习

## 从昨天的队列回到所有权

浅复制结构体时，整数成员各有一份，指针成员保存相同的地址。若两个结构体的 slots 指向同一分配，释放其中一侧后，通过另一侧继续读写会发生未定义行为。D19 的 queue_clone 先对目的队列分配独立槽位，再逐个复制有效样本。D20 的例子先把原队列内的 37 改成 50，再销毁原队列。快照保留 37。学生在比较两种复制方式后作答正确；曾误把“深拷贝”当成整个结构体的直接赋值。

对 D19 学生终稿的严格 C11 诊断指向第 6 行的未使用局部变量 a。学生保留循环所需的 num 并删除 a。教师用实际保存的 src 及原来测试入口复验成功。本册同时收录恢复出来的旧稿和学生修改的源码，其证据分别保留。

## 状态与返回值

`enum DeviceState device_step(enum DeviceState current, enum DeviceEvent event)` 中的返回类型和形参类型可以是同一种枚举。函数名是 device_step；current、event 是变量，BOOT、READY 等是枚举常量。C11 里枚举常量可以出现在 int 表达式中，类型声明本身不检查四态业务转移。返回的是由本次输入算出的下一状态，调用者赋回自己的变量，下一步才会使用它。

从 BOOT 处理 READY、START，保存每次返回值得到 IDLE、RUN。第一次只调用而漏存，调用者仍保存 BOOT，随后 START 保持 BOOT。教师对照实测。定义 first、second 时要给出合法事件值；若标识符根本没有声明，源文件在编译阶段失败。

## 指针与节点

下面是本日节点字段定义。value 装整数，next 装另一个 Node 的地址。

```c
struct Node {
    int value;
    struct Node *next;
};
```

设 `struct Node last = {37, NULL};`、`struct Node first = {12, &last};`、`struct Node *head = &first;`。`struct Node *p = head;` 将地址复制到 p，此时 p 和 head 都指向 first。`*p` 是节点本身，`p->value` 与 `(*p).value`、`first.value` 均为 12；`p->next` 是 &last。把 first.next 改为 NULL 后遍历，首节点仍输出 12，再沿 next 得到 NULL 并停止。

创建 `struct Node added = {8, head};` 时，两个初始化项按声明顺序写入 value 和 next。第一行后 head 仍指向 first。随后把 head 改为 &added，才得到 added、first、last 三节点链。如果此前已令 p = head，改变 head 不会改变 p 所保存的地址。

`struct Node *p = head;` 复制地址，使两个指针访问同一节点。若 head 指向有效节点，`struct Node copy = *head;` 复制节点，copy.value 和 copy.next 各占自己的成员位置；copy.next 里的地址仍指向与旧节点相同的后继。把结构体变量直接初始化为结构体指针会出现类型不匹配。

摘首测试要求旧首的 next 清空。保存后继地址后，旧首节点的连接可以独立更改。若调用者只向后移动链表入口，旧首的 next 仍指向剩余链，保留这个连接本身不会造成泄漏。头插、摘首两份学生原函数、失败稿和验收源码见本册的 C 原件。

## 申请、摘下和释放

头文件 stdlib.h 提供 malloc 和 free。malloc 接收要分配的字节数，成功时返回可用块的起始地址，失败时返回 NULL；成员初值由调用者设置。D19 的队列有 capacity 个整数槽位，D20 的首节点只有一个。两处各申请一块连续内存。

```c
q->slots = malloc(capacity * sizeof *q->slots);  // 元素数乘每个 int 的大小
struct Node *head = malloc(sizeof *head);        // 一个 Node 的大小
```

capacity 后面的星号是乘法。sizeof 括起来理解为 `sizeof(*q->slots)`，元素类型为 int；本题的这类 sizeof 操作只根据类型求大小，不读取申请前的指针。head 声明里的星号说明变量用来存地址。当前环境实测指针占 8 字节，Node 占 16 字节；具体大小以目标平台为准。节点的这块分配里同时包含 value 和 next 两个字段，next 指向的下一个节点另有存储。

以下是课堂完整调用者，配合学生已修订的头文件与 list_detach_front 构建。两个节点中的 last 是局部变量。

```c
#include "D20-list-node.h"
#include <stdio.h>
#include <stdlib.h>

int main(void)
{
    struct Node last = {37, NULL};
    struct Node *head = malloc(sizeof *head);
    if (head == NULL) return 1;
    head->value = 12;
    head->next = &last;
    struct Node *old = head;
    head = list_detach_front(head);
    free(old);
    printf("%d\n", head->value);
    return 0;
}
```

教师实测输出 37。old 保存原先那次 malloc 给出的地址，所以 free(old) 释放动态首节点。head 已改为 &last，不能交给 free。head->value 是整数，也不能传给 free。若漏掉 old 且原先没有其他可找到该块的有效指针，head 被改写后分配仍存在，程序再也找不到原地址，构成泄漏。只释放一次。局部指针变量自己的生命周期在离开块时结束，它也不会顺便释放所指对象；局部结构体 first 已经有空间，不需要 malloc 或 free。全局或 static 变量的生命周期持续到程序结束。

## 断点和构建

把等值的动态节点和 original 局部节点组成链，再摘首，停在 free(old) 前。教师 GDB 看到 old 和 head 所指对象的 value 都是 37，old == added 为真，head == &original 为真，old->next == NULL 为真。学生自行选 old == added，正确判断被释放的是原分配。此前状态机故障路径和断点 A 的逐项记录见原课堂日志。

Make 单目标短例为本册 D20-device.mk。第一条规则左边是待建的设备目标文件，右边是 C 源和公共头文件。Tab 起始的命令用 gcc -c 将源文件编译为对象。教师在副本先构建，再立即重跑，然后只更新头文件修改时间。首轮和第三轮调用编译器，第二轮显示 up to date。学生尚未回答只改枚举头是否重建以及原因，此处保留为 D21 的复习断点。
