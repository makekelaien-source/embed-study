#include <stdio.h>
int main (void) {
int readings [4] = {6, 9, 2,8};
for (int round = 0; round < 3; round ++)
{
    for ( int i = 0; i < 3 - round; i++)
{
    if (readings[i] > readings [i+1])
    {
        int temp = readings [i];
        readings[i] = readings [i+1];
        readings[i+1] = temp ;
       
    }        
}
}
for (int j = 0; j < 4; j++)
{
    printf("%d",readings[j]);
}
   
return 0;
}
