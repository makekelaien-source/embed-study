#include <stdio.h>

int main(void)
{
    int reading = 18;
    int target = 18;
    int position = -1;
    if (reading == target)
    {
        position = 0;
    }
    printf("%d\n", position);
    return 0;
}
