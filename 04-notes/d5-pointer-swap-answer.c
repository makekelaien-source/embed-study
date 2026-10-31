#include <stdio.h>

void swap(int *left, int *right)
{
    int temp = *left;
    *left = *right;
    *right = temp;
}

int main(void)
{
    int a = 3;
    int b = 8;

    printf("before: a=%d b=%d\n", a, b);
    swap(&a, &b);
    printf("after: a=%d b=%d\n", a, b);
    return 0;
}
