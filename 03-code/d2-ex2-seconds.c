/*
 * d2-ex2-秒数换算.c
 *
 * 题目：用 scanf 读入一个总秒数（比如 7384），
 *       把它换算成「几小时几分几秒」，打印出来。
 *
 * 样例：输入 7384  ->  输出 2 小时 3 分 4 秒
 *
 * 提示：1 小时 = 3600 秒，1 分钟 = 60 秒
 *       小时 = 总秒数 / 3600
 *       剩下 = 总秒数 % 3600     （% 是取「除完剩下的」）
 *       分钟 = 剩下 / 60
 *       秒   = 剩下 % 60
 *
 * 编译运行：go d2-ex2-秒数换算
 */
#include <stdio.h>

int main(void)
{
    int total;       /* 总秒数 */
    int h, m, s;     /* 时、分、秒 */

    printf("请输入总秒数: ");
    scanf("%d",&total) ;
    h = total / 3600 ;
    m = total % 3600 / 60 ;
    s = total % 3600 % 60 ; /* TODO: 用 scanf 读入 total（别忘了 &） */


    /* TODO: 用 / 和 % 算出 h、m、s */


    printf("%d 小时 %d 分 %d 秒\n", h, m, s);

    return 0;
}
