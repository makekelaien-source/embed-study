/* Teacher demonstration: single input, int-range values, no trailing spaces.
   Full solution shown on request; not independent student work. */
#include <stdio.h>

int main(void)
{
    int a;
    char tail;
    printf("请输入一个整数，输入后直接回车\n");
    int b = scanf("%d%c", &a, &tail);
    if (b == 2 && tail == '\n')
    {
        printf("%d\n", a);
    }
    else
    {
        printf("输入格式不符合要求\n");
    }
    return 0;
}
