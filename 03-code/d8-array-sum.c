#include <stdio.h>
int main (void) {
int readings [4] = {6, 9, 2,8};
int total = 0;
for ( int i = 0; i < 4; i++)
{
    printf ("%d\n",readings[i]);
    total += readings[i] ;

}
printf("%d",total);
return 0;
}
