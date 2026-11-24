# D19｜运行时申请槽位

L5 动态内存基本原则。教师最小示例约定容量为 1 到 8；实际容量由调用方传入。申请的字节数是元素数量乘单个元素大小。成功返回地址，槽值未初始化；失败返回 NULL。释放后不再访问或重复释放。队列的逻辑数量仍由调用者单独维护。

~~~c
#include <stdio.h>
#include <stdlib.h>

/* The caller supplies a capacity from 1 to 8. */
static void demo(size_t capacity)
{
    int *slots = malloc(capacity * sizeof *slots);
    if (slots == NULL) {
        puts("allocation failed");
        return;
    }

    slots[0] = 20;
    printf("%d\n", slots[0]);
    free(slots);
}

int main(void)
{
    demo(3);
    demo(5);
    return 0;
}
~~~

教师严格 C11 实测两次均输出 20，仅验证成功路径。首个预测见课堂。
