#include <stdio.h>
int swap (int *left, int *right){
    int p = *left;
    *right = &p ;
    left = right ;
}

int main(void){
    int a = 3 ; int b = 8 ;
    swap (a,b) ;
    printf ("%d%d",a,b);
    return 0;
}