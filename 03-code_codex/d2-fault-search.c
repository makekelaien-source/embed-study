#include <stdio.h>
int main(void)
{
    int sample[5] = {23,-999,25,-999,24}; int answer = -1 ;
    for (int  i = 0; i < 5; i++)
    {
        if (sample [i] != -999)
        {
        }else if (sample [i] == -999)
        {
            answer = i ;
            break;  
        }      
    }
    printf("%d",answer);
    return 0 ; 
}