/* d3-ex2.c - 练习2: 气温分档（else if 顺序练习）
 * 用到讲义: 第4节 else if（先严格后宽松）
 * 规则: >=30 炎热, >=20 舒适, >=10 偏凉, 其余 寒冷
 * 测试输入: 35 -> 炎热   22 -> 舒适   15 -> 偏凉   5 -> 寒冷
 */
#include <stdio.h>

int main(void)
{
    int t = 0;

    printf("请输入气温(整数): ");
    scanf("%d", &t);

    if(t >= 40){
        printf("酷暑");
    }else if (t >= 30){
        printf("炎热");/* code */
    }else if (t >= 20){
        printf("舒适");/* code */
    }else if (t >= 10){
        printf("偏冷");/* code */
    }else {
        printf ("寒冷");
    }
    
    

    return 0;
}
