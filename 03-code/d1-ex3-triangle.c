#include <stdio.h>

int main(void)
{
    float weight, height ;
    printf("你的身高是()cm\n") ;
    scanf("%f", &height) ;
    weight = (height-100)*2 ;
    printf("你的理想体重是%.1f斤",weight) ;
    return 0l ;
}
