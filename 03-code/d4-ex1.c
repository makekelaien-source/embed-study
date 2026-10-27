#include <stdio.h>

int main(void)
{
    int day = 0 ;
    printf ("请输入1-7.\n") ;
    scanf ("%d",&day) ;
    switch (day)
    {
    case 1:
    printf("今天是星期一") ;
    case 2:
    printf("今天是星期二") ;
        break;
    case 3:
    printf("今天是星期三") ;
        break;
    case 4:
    printf("今天是星期四") ;
        break;
    case 5:
    printf("今天是星期五") ;
        break;
    case 6:
    printf("今天是星期六") ;
        break;
    case 7:
    printf("今天是星期日") ;
        break;
    default:
    printf("输入错误");
        break;
    } 
    return 0 ;
}