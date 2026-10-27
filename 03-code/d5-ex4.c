/*
 * d5-ex4 练习题：break 和 continue 专项
 *
 * 题目：不断读入整数，直到读入 -1 为止（-1 是停止信号，不参与统计）。
 *   - 读入 0：用 continue 跳过，不计入统计
 *   - 读入 -1：用 break 立刻结束循环
 *   - 其他数：累加到 sum，并让 cnt 加 1
 * 循环结束后打印：共统计了多少个数、它们的和。
 *
 * 运行效果示例（> 后面是你敲的内容）：
 *   请输入数字: > 5
 *   请输入数字: > 0
 *   请输入数字: > 7
 *   请输入数字: > -1
 *   共统计 2 个数, 和为 12
 *
 * 要求：
 *   1. 用 while 循环
 *   2. 必须出现 break 和 continue 各一次
 *   3. 先写框架再填细节: 读入 -> 判断 -1 退出 -> 判断 0 跳过 -> 累加
 *
 * 用到今天讲义的哪几条:
 *   - while 循环（次数未知，靠信号停止）
 *   - break: 立刻离开整个循环
 *   - continue: 只跳过本轮剩下的代码, 直接下一轮
 *   - scanf 的 &、计数器 cnt++、累加 sum = sum + x
 */

#include <stdio.h>

int main(void)
{
    int n ; int sum = 0 ; int cnt = 0 ;
    while (1)
    {
        printf("请输入数字\n");
        scanf("%d",&n);
        if ( n == -1)
        {
            break;
        } if ( n == 0 )
        {
            continue;
        }

        sum = sum + n;
        cnt ++;
        
    }
    printf("共统计%d个数,和为%d",cnt,sum);

    return 0;
}
