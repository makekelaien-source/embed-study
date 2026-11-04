/* Teacher-only answer; do not show before student attempt/request. */
#include <stdio.h>
#include "d9-reference-helpers.h"
int read_text(char *dest, int capacity) {
    if (capacity < 2) return -1;
    dest[0] = '\0';
    if (fgets(dest, capacity, stdin) == NULL) return 0;
    int pos = find_char_index(dest, capacity, '\n');
    if (pos >= 0) {
        dest[pos] = '\0';
        return 1;
    }
    return 2;
}
int main(void) {
    char text[8];
    int status = read_text(text, sizeof text);
    printf("STATUS=%d\n", status);
    if (status > 0) printf("TEXT=[%s]\n", text);
    return 0;
}
