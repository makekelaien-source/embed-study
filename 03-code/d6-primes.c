#include <stdio.h>
int main(void)
{
    int i  ; int j = 1; int cnt = 0 ;
    for ( i = 2; i < 100; i++)
    {
        for ( j = 2; j <= i; j++)
        {
            if (i % j == 0 )
            {
                break;
            }
                
        }
    if (i == j)
    {
        cnt ++;
        printf ("%d\n",i);
    }
    
    
    }
    printf("%d",cnt);
    return 0;
    
}