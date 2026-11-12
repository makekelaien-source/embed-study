#include <stdio.h>
int main(void) {
    unsigned int flags = 1, mask = 3;
    int any = (flags & mask) != 0;
    int all = (flags & mask) == mask;
    printf("partial=%d,%d\n", any, all);
    flags = 3;
    printf("complete=%d,%d\n", (flags & mask) != 0, (flags & mask) == mask);
    return 0;
}
