#include <stdio.h>
int main(void)
{
    int sum = 0; int number = 0; float average = 0 ; int cnt = 0;
    printf("请输入整数\n");
    scanf("%d",&number);
    while (number >= 0)
    {
        sum = sum + number ;
        cnt ++;
        printf ("您输入了%d,目前综合为%d\n",number,sum);
        scanf("%d",&number);
    }
    if (number < 0){
        average = (float) sum / cnt;
        cnt ++;
        printf("您输入了负数，循环结束，目前总计%d，循环%d次\n",sum,cnt);
        printf("输出和%d,个数%d,平均数%.1f",sum ,cnt,average);
    }
    return 0 ;
}