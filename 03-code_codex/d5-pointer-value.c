#include <stdio.h>
int main(void){
    int reading = 18 ;
    int backup = reading ;
    int *p = &reading ;
    *p = 5 ;
    printf("%d%d%d",reading,backup,*p);
}