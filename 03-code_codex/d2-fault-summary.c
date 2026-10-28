#include <stdio.h>
int main(void)
{
    int a = 0 ; int location = -1 ;
    int sample [5] = {23,-999,25,-999,24};
    for (int i = 0; i < 5; i++)
    {
        if (sample[i] == -999)

        {
            location = i;
            break;
        }
        
        
    }
    for (int i = 0; i < 5; i++)
    {
        if (sample[i] == -999)

        {
            a++;
        }
        
        
    }
    printf ("%d\n%d",a,location);
    return 0 ;
}    