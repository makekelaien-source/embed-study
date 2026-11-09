#include <stdio.h>
#include <string.h>
#include "d13-mode-command.h"

int main(void)
{
    char text[16];

    while (fgets(text, sizeof text, stdin) != NULL) {
        char *newline = strchr(text, '\n');
        if (newline != NULL) {
            *newline = '\0';
        }
        printf("%d\n", classify_mode(text, sizeof text));
    }

    if (ferror(stdin)) {
        puts("READ_ERROR");
        return 1;
    }
    return 0;
}
