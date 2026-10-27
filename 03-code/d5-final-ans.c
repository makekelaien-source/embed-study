/* 标准答案: 判断一个数是不是素数 */
#include <stdio.h>

int main(void)
{
    int num, i;

    printf("input a number: ");
    scanf("%d", &num);

    /* 从 2 开始, 一路试除到 num-1 */
    for (i = 2; i < num; i++) {
        if (num % i == 0) {   /* 找到因子, 不用再试了 */
            break;
        }
    }

    /* 循环结束后才下结论 */
    if (i == num) {
        printf("%d is prime\n", num);
    } else {
        printf("%d is not prime\n", num);
    }
    return 0;
}
