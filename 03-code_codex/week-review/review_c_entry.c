/* Teacher entry: run at most two reads from the same stream. */
#include <stdio.h>
#include "review_input.h"

int main(void)
{
    char text[8];
    for (int call = 0; call < 2; call++) {
        int status = read_command(text, sizeof text);
        printf("STATUS=%d\n", status);
        if (status == 1) {
            printf("TEXT=[%s]\n", text);
        }
        if (status <= 0 || status == 3) {
            break;
        }
    }
    return 0;
}
