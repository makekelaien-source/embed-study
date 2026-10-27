#include <stdio.h>
int main (void) {
int readings [4] = {6, 9, 2,8};
int total = 0; int max = readings[0];
for ( int i = 0; i < 4; i++)
{
    printf ("%d\n",readings[i]);
    total += readings[i] ;
    if (max > readings [i])
    {
        max = max ;
    }else max = readings[i];


}
printf("总和%d,其中最大数%d",total,max);
return 0;
}
