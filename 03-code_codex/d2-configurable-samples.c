#include <stdio.h>
#define SAMPLE_COUNT 5

int is_fault (int value)
{
    if (value == -999)
    {
        return 1;
    }else return 0;
    
}

int main(void)
{
int a = 0 ; int location = -1 ; int cnt = 0; int sum = 0; float ave = 0 ;
int sample [SAMPLE_COUNT] = {23,-999,25,-999,24};
    for (int i = 0; i <SAMPLE_COUNT; i++)
    {
        if (is_fault(sample[i]) == 1)
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
            printf ("%d\n%d\n%d\n无有效数据",SAMPLE_COUNT, a, sum);
            return 0 ;
        }
    printf ("%d\n%d\n%d\n%.2f", cnt , a , sum , ave);
    return 0 ;
}    