# D20｜L6 单链表入门

一个节点保存整数和下一节点的地址。head 指向首节点，空链表的 head 为 NULL。末节点的 next 为 NULL。p 从 head 开始，每轮读取当前值后沿 next 前进，p 为 NULL 时停止。只在 p 指向有效节点时读取其成员。移动局部指针 p 时，head 和节点字段保持原值。例中的两个局部节点在 main 执行期间有效。

```c
#include <stdio.h>
struct Node {
    int value;
    struct Node *next;
};
int main(void) {
    struct Node last = {37, NULL};
    struct Node first = {12, &last};
    struct Node *head = &first;
    struct Node *p = head;
    while (p != NULL) {
        printf("%d\n", p->value);
        p = p->next;
    }
    return 0;
}
```

教师严格 C11 实测输出两行 12、37。理解检查：若只把 first.next 改为 NULL 后再从 head 遍历，预测访问哪些节点并解释停止原因。
头插已有节点：从完整的 12、37 链开始，struct Node added = {8, head}; 将旧入口保存到新节点的 next。再执行 head = &added;。added 仍在作用域内时从新入口遍历，教师实测输出 8、12、37。空链时旧入口为 NULL，同样成立。
摘下首节点：调用者保存旧入口，节点在调用者的作用域内有效。仅移动 head 时 old->next 仍指向后继。list_detach_front 的验收是返回剩余链的首节点地址、旧首节点 next 归空、其余链接与所有 value 保持，空链返回 NULL。教师已验证移动入口短例和测试入口分编译。
生命周期对照：malloc 分配的首节点连向仍在作用域内的局部尾节点 last。调用者先用 old 保存首节点地址，再摘下并用 free(old) 释放该次分配。剩余入口等于 &last，教师实测 head->value 为 37。
