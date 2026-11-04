#include <stdio.h>
int main(void) {
    char text[8];
    if (fgets(text, sizeof text, stdin) == NULL) {
        puts("READ_FAILED");
        return 0;
    }
    printf("TEXT=[%s]\n", text);
    return 0;
}
