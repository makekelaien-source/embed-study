/* d3-demo.c - if/else 分支示范（D3 讲义配套） */
#include <stdio.h>

int main(void)
{
    int n = 0;
    int score = 0;
    int attendance = 0;

    /* 第 1 段: if / else 判断奇偶 */
    printf("请输入一个整数: ");
    scanf("%d", &n);

    if (n % 2 == 0) {
        printf("%d 是偶数\n", n);
    } else {
        printf("%d 是奇数\n", n);
    }

    /* 第 2 段: else if 成绩分档 */
    printf("请输入成绩(0-100): ");
    scanf("%d", &score);

    if (score >= 90) {
        printf("优秀\n");
    } else if (score >= 60) {
        printf("及格\n");
    } else {
        printf("不及格\n");
    }

    /* 第 3 段: && 组合条件 */
    printf("请输入出勤率(0-100): ");
    scanf("%d", &attendance);

    if (score >= 60 && attendance >= 80) {
        printf("可以参加考试\n");
    } else {
        printf("不能参加\n");
    }

    return 0;
}
