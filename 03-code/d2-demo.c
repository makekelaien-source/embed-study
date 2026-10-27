/*
 * d2-demo-运算符.c —— 运算符与类型转换「先猜后验证」练习
 *
 * 玩法：每个 printf 里有个 ____，先用手算填上你的答案，
 *       再编译运行，看猜对没有。猜错的地方就是知识漏洞。
 *
 * 编译运行：在 03-code 文件夹里输入  go d2-demo-运算符
 */
#include <stdio.h>

int main(void)
{
    int   a = 7, b = 2;
    float x = 7.0f, y = 2.0f;

    /* ---- 第一组：整数运算 ---- */
    printf("a + b = %d\n", a + b);
    printf("a - b = %d\n", a - b);
    printf("a * b = %d\n", a * b);
    printf("a / b = %d   <-- 我猜是 _3___, 实际是 __3__\n", a / b);
    printf("a %% b = %d  <-- %% 是1取余数\n", a % b);

    /* ---- 第二组：带小数的运算 ---- */
    printf("x / y = %.2f\n", x / y);
    printf("a / b 强转 = %.2f\n", (float)a / b);
    printf("直接 a/b 再给 float = %.2f  <-- 为什么不是 3.50?\n", (float)(a / b));

    /* ---- 第三组：赋值时的隐式转换 ---- */
    int   m = 3;
    float n = 5.5f;
    printf("m = %d\n", m);
    printf("n = %f\n", n);
    n = m;          /* int 放进 float 盒子 */
    printf("n 变成 %f\n", n);
    m = 3.9;        /* float 放进 int 盒子：小数被砍，不是四舍五入 */
    printf("m 变成 %d  <-- 我猜是 ____, 实际是 ____\n", m);

    /* ---- 第四组：比较和逻辑（结果是 1 真 或 0 假）---- */
    printf("a == 7 是 %d\n", a == 7);
    printf("a != 7 是 %d\n", a != 7);
    printf("a > b && b > 0 是 %d\n", a > b && b > 0);
    printf("a > b || a < 0 是 %d\n", a  > b || a < 0);

    /* ---- 第五组：自增自减 ---- */
    int i = 5;
    i++;            /* i 变成 6 */
    i += 3;         /* i 再加 3 */
    printf("i = %d\n", i);

    return 0;
}
