#include <stdio.h>
int main(void)
{
    int num ; int i ;
    printf("请输入一个数,我会帮你判断它是否是素数\n");
    scanf("%d",&num);
    
        for ( i = 2 ; i <= num; i++)
        {
            if ( num % i != 0 )
            {
                printf("这个数是素数");
                break;
            } else {printf("这个数不是素数");
            break;
        }}
        if (num <=1)
        {
            printf("这个数不是素数");
        }
        
        
    return 0 ;
    
    
}