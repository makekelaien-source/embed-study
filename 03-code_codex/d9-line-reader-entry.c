/* Teacher harness: student writes only d9-line-reader.c. */
#include <stdio.h>
#include "../04-notes/next-day-demo/d9-reference-helpers.h"
#include "d9-line-reader.c"

int main(void)
{
    char text[8];
    int status = read_text(text, sizeof text);
    printf("STATUS=%d\n", status);
    if (status == 1 || status == 2) {
        printf("TEXT=[%s]\n", text);
    }
    return 0;
}
