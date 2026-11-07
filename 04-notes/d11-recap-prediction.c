#include <stdio.h>
#include "d11-token-prefix.h"
#include "d11-after-delimiter.h"

int main(void)
{
    char text[] = "AB/CD";
    int length = token_prefix_length(text, sizeof text, '/');
    const char *suffix = after_delimiter(text, sizeof text, '/');
    printf("%d %s\n", length, suffix);
    text[suffix - text] = 'X';
    printf("%c %c\n", *suffix, suffix[1]);
    return 0;
}
