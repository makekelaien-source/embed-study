#include <stdio.h>
int main(void)
{
    void area (int w, int h){
        printf("面积是%d*%d\n",w,h);
    }
    area (3,5);
    area (4,6);
    return 0;
}