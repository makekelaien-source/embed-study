#include <stdio.h>

int main(void)
{
    int current = 2;
    int longest = 2;
    current = 0;
    current++;
    if (current > longest)
    {
        longest = current;
    }
    printf("%d %d\n", current, longest);
    return 0;
}
