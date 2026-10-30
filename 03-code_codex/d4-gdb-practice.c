#include <stdio.h>

int add(int left, int right)
{
    return left + right;
}

int main(void)
{
    int values[3] = {2, 5, -3};
    int total = 0;

    for (int i = 0; i < 3; i++)
    {
        total = add(total, values[i]);
    }

    printf("total=%d\n", total);
    return 0;
}
