#include <stdio.h>

int main(void)
{
    char line[] = "MODE AUTO";
    const char *part = line + 5;
    printf("%s\n", part);
    line[5] = 'X';
    printf("%s\n", part);
    return 0;
}
