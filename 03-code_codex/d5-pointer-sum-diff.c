#include <stdio.h>
void calculate (int a, int b,int *sum,int *diff){
    *sum = a + b;
    *diff = a - b;
}

int main(void){
    int x = 7; int y = 3;
    int sum ;int diff ;
    calculate (x,y,&sum,&diff);
    printf("%d %d",sum,diff);
    return 0;
}