#include <stdio.h>

int double_value(int value);

int main(void)
{
    printf("%d\n", double_value(4));
    return 0;
}

int double_value(int value)
{
    return value * 2;
}
