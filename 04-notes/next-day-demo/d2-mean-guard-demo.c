#include <stdio.h>

int main(void)
{
    int total = 7;
    int valid_count = 2;
    if (valid_count > 0)
    {
        printf("%.2f\n", (float)total / valid_count);
    }
    else
    {
        printf("no valid data\n");
    }
    return 0;
}
