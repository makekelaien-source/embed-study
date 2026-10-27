#include <stdio.h>

int main(void)
{
    float area, height, volume;
    printf("请输入三棱锥的底和高");
    scanf("%f%f",&area,&height);
    volume=area*height/3;
    printf("三棱锥的体积是%f",volume);
    return 0 ;
}