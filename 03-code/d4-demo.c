/* d4-demo.c - switch + for 示范
 * 编译: .\go d4-demo   (在 03-code 目录下)
 */
#include <stdio.h>

int main(void)
{
    /* ---------- 第一部分: switch 星期几 ---------- */
    int day = 0;
    printf("请输入 1~7: ");
    scanf("%d", &day);

    switch (day) {
        case 1:
            printf("星期一, 开工\n");
            break;
        case 2:
            printf("星期二\n");
            break;
        case 3:
            printf("星期三\n");
            break;
        case 4:
            printf("星期四\n");
            break;
        case 5:
            printf("星期五\n");
            break;
        case 6:
            printf("星期六, 练习日\n");
            break;
        case 7:
            printf("星期日\n");
            break;
        default:
            printf("输入无效, 请输入 1~7\n");
            break;
    }

    /* ---------- 第二部分: for 求 1+2+...+100 ---------- */
    int i = 0;
    int sum = 0;

    for (i = 1; i <= 100; i = i + 1) {
        sum = sum + i;
    }
    printf("1+2+...+100 = %d\n", sum);

    return 0;
}
