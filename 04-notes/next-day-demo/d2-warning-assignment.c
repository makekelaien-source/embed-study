/* Intentional warning for a diagnostic-reading lesson. */
#include <stdio.h>

int main(void)
{
    int count = 0;
    if (count = 1)
    {
        printf("found\n");
    }
    printf("%d\n", count);
    return 0;
}
