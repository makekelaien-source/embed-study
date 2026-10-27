/*
 * d2-ex1-交换两个数.c
 *
 * 题目：程序里有两个 int：a = 3, b = 8。
 *       把它们交换，最后打印 a=8 b=3。
 *
 * 提示：交换两杯水必须找第三个空杯：
 *       tmp = a;  a = b;  b = tmp;
 *
 * 选做（挑战）：不用第三个变量，只用加减法交换（见笔记第四节）。
 *
 * 编译运行：go d2-ex1-交换两个数
 */
#include <stdio.h>

int main(void)
{
    int a = 3;
    int b = 8;

    printf("交换前: a=%d b=%d\n", a, b);

    float c ;
    c = a ;
    a = b ;
    b = c ;

    printf("交换后: a=%d b=%d\n", a, b);  /* 期望输出 a=8 b=3 */

    return 0;
}
