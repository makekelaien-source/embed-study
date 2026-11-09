#include <string.h>

void trim_right_spaces(char *text)
{
    const char *p = strchr(text, ' ');

    while (p != NULL) {
        const char *start = p;

        while (*p == ' ') {
            ++p;
        }

        if (*p == '\0') {
            text[start - text] = '\0';
            return;
        }

        p = strchr(p, ' ');
    }
}
