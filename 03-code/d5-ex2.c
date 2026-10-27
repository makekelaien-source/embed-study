#include <stdio.h>
int main(void)
{
    int balance = 100; int bottom = 0 ; int add = 0;
    do
    {
        printf("1 查询余额\n2 存款\n3 退出\n");
        scanf("%d",&bottom);
        
        switch (bottom){
    case 1:
        printf ("余额为%d\n",balance);
        break;
    
    case 2:
        printf ("要存入多少元\n");
        scanf("%d",&add);
        printf ("余额为%d\n",(int) balance + add);
        balance = balance + add ;
        break;
    case 3:
        printf("欢迎下次光临\n");
    default :
    printf("没有这个选项");
    }
    } while ( bottom != 3);
    return 0 ;
}