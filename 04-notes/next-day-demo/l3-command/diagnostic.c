#include <stdio.h>

int main(void)
{
    int line_number = 3;

    puts("READY");
    fprintf(stderr, "line %d: BAD_COMMAND\n", line_number);
    return 0;
}
