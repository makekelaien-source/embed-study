#include <stdio.h>

int main(void)
{
    int temperature = 25;
    int backup = temperature;
    printf("before value=%d address=%p backup=%d\n",
           temperature, (void *)&temperature, backup);
    temperature = 30;
    printf("after value=%d address=%p backup=%d\n",
           temperature, (void *)&temperature, backup);
    return 0;
}
