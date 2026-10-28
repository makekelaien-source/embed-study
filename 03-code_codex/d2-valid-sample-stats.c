#include <stdio.h>

int main(void)
{
int a = 0 ; int location = -1 ; int cnt = 0; int sum = 0; float ave = 0 ;
int sample [5] = {23,-999,25,-999,24};
    for (int i = 0; i <5; i++)
    {
        if (sample [i] == -999)
        {
            cnt ++;
            if (location  == -1 )
            {
                location = i;
            }

            
        }else {sum += sample[i] ;
            a++;
            ave = (float) sum / a ;
        }

        
        
    }
            if ( a == 0 )
        {
            printf ("5\n0\n0\n无有效数据");
            return 0 ;
        }
    printf ("%d\n%d\n%d\n%.2f", cnt , a , sum , ave);
    return 0 ;
}    