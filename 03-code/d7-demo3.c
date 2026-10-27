#include <stdio.h>

/* 方式1: int 函数 - 自己不算打印, 把数字"寄回来", 由调用的人打印 */
int area_calc(int w, int h)
{
    return w * h;              /* 寄回 15, 同时关门 */
}

/* 方式2: void 函数 - 自己在函数里打印, 不寄回任何东西 */
void area_print(int w, int h)
{
    printf("面积 = %d\n", w * h);   /* 函数内部自己打印 */
}

int main(void)
{
    int s;

    s = area_calc(3, 5);       /* 寄回来的 15 必须用 s 接住 */
    printf("s = %d\n", s);     /* 调用的人负责打印 */

    area_print(4, 6);          /* 它自己打印, 没有东西要接 */

    /* 寄回来的数字也可以不接, 直接塞进 printf 的 %d 坑位 */
    printf("直接打印: 面积 = %d\n", area_calc(2, 7));
    return 0;
}
