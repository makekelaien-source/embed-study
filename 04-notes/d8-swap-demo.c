/* Teacher example: preserve a value before overwriting it. */
#include <stdio.h>

int main(void)
{
    int a = 6;
    int b = 9;
    int temp = a;
    a = b;
    b = temp;
    printf("%d %d\n", a, b);
    return 0;
}
