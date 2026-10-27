#include <stdio.h>
int main(void)
{
    int level = 0 ; int answer; int yes ;
    printf ("请选择难度：\n1.简单\n2.中等\n3.困难");
    scanf ("%d",&level);

    do
    {
        int cnt = 0 ;    
        while (1)
    {
    switch (level)
    {
    case 1:
        printf ("范围为1~50\n");
        scanf ("%d",&answer);
        while (answer == 42)
        {
            printf ("回答正确！");
            cnt++;
            break;
        }if (answer != 42){
            printf ("回答错误，请重新回答！\n") ;
            if (answer > 42)
            {
                printf ("猜大了！\n") ;
            } else printf ("猜小了！\n");
            cnt++;
        continue;
        }     
        break;    
     
    case 2:
        printf ("范围为1~100\n");
        scanf ("%d",&answer);
        while (answer == 77)
        {
            printf ("回答正确！");
            cnt++;
            break;
        }if (answer != 77){
            printf ("回答错误，请重新回答！\n") ;
            if (answer > 77)
            {
                printf ("猜大了！\n") ;
            } else printf ("猜小了！\n");
            cnt++;
        continue;
        } 
        break;
    case 3:
        printf ("范围为1~1000\n");
        scanf ("%d",&answer);
        while (answer == 385)
        {
            printf ("回答正确！");
            cnt++;
            break;
        }if (answer != 385){
            printf ("回答错误，请重新回答！\n") ;
            if (answer > 385)
            {
                printf ("猜大了！\n") ;
            } else printf ("猜小了！\n");
            cnt++;
        continue;
        } 
        break;
    default:
        printf("输入错误，请重新选择");
        scanf("%d", &level);    
        continue;
    }
    break;
}

    printf ("总次数%d\n",cnt);
    if (cnt <= 5)
    {
        printf ("大神！\n") ;
    }else if (cnt <= 10)
    {
        printf ("不错！\n") ;
    }else printf ("有点慢\n");
    printf ("1 再来一局 0 结束游戏");
    scanf("%d",&yes);
    } 
    
    while (yes == 1);
    
    return 0 ;
}