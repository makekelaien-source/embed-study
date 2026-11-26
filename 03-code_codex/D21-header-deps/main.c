#include "limit.h"
#include <stdio.h>

int main(void)
{
    int actual = is_warm(31);
    int expected = (31 >= WARM_LIMIT);

    printf("limit=%d actual=%d expected=%d\n", WARM_LIMIT, actual, expected);
    if (actual == expected) {
        puts("HEADER_DEP_CHECKS=PASS");
        return 0;
    }
    puts("HEADER_DEP_CHECKS=FAIL");
    return 1;
}
