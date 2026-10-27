#include <stdio.h>

int main(void)
{ 
    int i = 0; int sum = 0;
    for (i = 1; i <= 100; i++)
    {sum = sum + i ;
        /* code */
    }
    printf ("1+2+..+100=多少\n");
    scanf ("%d",&sum);
    switch (sum)
    {
    case 5050:
        printf ("回答正确！");
        break;
    
    default:
        printf ("回答错误！");
        break;
    } 
    return 0 ;
}