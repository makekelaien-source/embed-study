/* d3-ex1.c - 练习1: 判断奇偶（负数也要对）
 * 用到讲义: 第3节 if/else, 第6节骨架
 * 要求: 判断奇数写 n % 2 != 0, 不要写 == 1（今天刚补的坑）
 * 测试输入: 7 -> 奇数   8 -> 偶数   -7 -> 奇数
 */
#include <stdio.h>

int main(void)
{
    int n = 0;

    printf("请输入一个整数: ");
    scanf("%d", &n);

    if (n % 2 != 0/* TODO: 判断 n 是奇数 */){
        printf("%d 是奇数\n", n);
    } else {
        printf("%d 是偶数\n", n);
    }

    return 0;
}
