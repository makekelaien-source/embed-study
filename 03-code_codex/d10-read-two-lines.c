#include <stdio.h>

int main(void)
{
    char text[8];
    if (fgets(text, sizeof text, stdin) == NULL) {
        return 0;
    }
    printf("COMMAND %s", text);

    if (fgets(text, sizeof text, stdin) != NULL) {
        printf("VALUE %s", text);
    } else {
        puts("MISSING VALUE");
    }

    return 0;
}
