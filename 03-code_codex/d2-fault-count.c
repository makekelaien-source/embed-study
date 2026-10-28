#include <stdio.h>
int main(void)
{
    int sample [5] = {23,-999,25,-999,24};
    int a = 0 ;
    for ( int i = 0; i < 5; i++)
    {
        if ( sample[ i] == -999)
        {
            a++;
        }
        
    }
    printf ("%d",a);
    return 0 ;
}