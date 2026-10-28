#include <stdio.h>
int main(void)
{
    int a[5] = {14,7,14,3,9};
    int target = 8 ;
    int position = -1 ;
  
    for ( int b = 0; b < 5; b ++)
    {
        if (a [b] == target)
        {
            
            position = b ;
            break;
        }
        
        
    }printf("%d\n",position);
    return 0 ;
}