/* Teacher harness; student writes set_switch in a separate source file. */
#include <stdio.h>
unsigned int set_switch(unsigned int flags, unsigned int mask, int enabled);
int main(void) {
    unsigned int flags = 3;
    unsigned int result = set_switch(flags, 4, 1);
    printf("original=%u result=%u\n", flags, result);
    flags = result;
    flags = set_switch(flags, 2, 0);
    printf("flags=%u\n", flags);
    return 0;
}
