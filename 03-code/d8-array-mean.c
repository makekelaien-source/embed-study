#include <stdio.h>
int main (void) {
int readings [4] = {-2, -8, -9,-1};
int total = 0; int max = readings[0];
for ( int i = 0; i < 4; i++)
{
    printf ("%d\n",readings[i]);
    total += readings[i] ;
    if (max > readings [i])
    {
    }else max = readings[i];


}
printf("总和%d,其中最大数%d,平均值为%.2f",total,max,(float) total / 4);
return 0;
}
