/* Teacher harness. Link existing l4-switch-flags.c and the new student source. */
#include <stdio.h>
#include "l4-switch-at.h"
int main(void) {
    unsigned int flags = 0;
    flags = set_switch_at(flags, 2, 1);
    printf("%u\n", flags);
    flags = set_switch_at(flags, 0, 1);
    printf("%u\n", flags);
    flags = set_switch_at(flags, 2, 0);
    printf("%u\n", flags);
    return 0;
}
