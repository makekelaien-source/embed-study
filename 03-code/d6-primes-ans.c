/* 标准答案: 打印 100 以内所有素数 */
#include <stdio.h>

int main(void)
{
    int i, j;

    for (i = 2; i < 100; i++) {      /* 外层: 逐个检查 2..99 */
        for (j = 2; j < i; j++) {    /* 内层: 用 2..i-1 试除 i */
            if (i % j == 0) {
                break;               /* 有因子, 不是素数 */
            }
        }
        if (j == i) {                /* 内层走完全程没 break => 素数 */
            printf("%d\n", i);
        }
    }
    return 0;
}
