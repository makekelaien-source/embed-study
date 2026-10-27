#include <stdio.h>

// ---- 演示 4: 为什么要用函数, 不直接写 printf ----
void line(void)                 // 分隔线这张 "详图" 只画一次
{
    printf("================\n");
}

// ---- 演示 5: 复印件是函数里的原材料 ----
int abs_value(int n)            // n 是递进来原件的复印件
{
    if (n < 0) {
        n = -n;                 // 在复印件上加工, 放心改, 不伤原件
    }
    return n;                   // 把加工好的结果交出去
}

int main(void)
{
    // 想画 3 条分隔线: 调用 3 次就行, 每张都是一行
    line();
    printf("score\n");
    line();
    printf("math 90\n");
    line();

    int b = -7;
    int r = abs_value(b);       // 把 b 复印一份递进去
    printf("b = %d, r = %d\n", b, r);
    return 0;
}
