#include <stdio.h>
int main(void)
{
    int max (int a, int b){
        if (a > b )
        {
            printf("%d",a);
        }else if (b > a)
        {
            printf("%d",b);
        }else printf ("他俩一样大");
    
    }
    int c; int d ;
    
    printf("输入两个数比大小\n");
    
    scanf ("%d%d",&c,&d);
    
    max (c,d);
    
    return 0 ;
}