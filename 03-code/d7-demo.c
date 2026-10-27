#include <stdio.h>

// ---- 演示 1: void = 不交结果 ----
void hello(void)          // 开头 void: 不交结果; 括号 void: 不递东西
{
    printf("hello!\n");   // 只干活, 没有 return 值
}

// ---- 演示 2: return 一执行, 函数立刻结束 ----
int pick(int n)
{
    printf("A\n");        // 会打印
    return n;             // 下班! 函数到此结束
    printf("B\n");        // 永远打印不出来, 因为上面已经 return 了
}

// ---- 演示 3: 递进去的是复印件 ----
void try_change(int n)    // n 是复印件
{
    n = 100;              // 只改复印件
}

int main(void)
{
    hello();              // void 函数: 直接调用, 不能用变量接

    int r = pick(5);      // int 函数: 用变量接住结果
    printf("pick back = %d\n", r);

    int a = 5;
    try_change(a);
    printf("a = %d\n", a);   // 还是 5, 原件没动
    hello();
    return 0;
}
