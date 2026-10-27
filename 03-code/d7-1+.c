#include <stdio.h>
int main (void)
{
    int a ;
    printf ("请输入一个整数\n");
    int b = scanf ("%d",&a);
    if (b == 1)
    {
        printf("%d",a);
    }else printf("输入的不是整数");
    
    return 0;
}