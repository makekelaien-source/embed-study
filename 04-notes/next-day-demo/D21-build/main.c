#include "sample.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
    assert(is_warm(29) == 0);
    assert(is_warm(30) == 1);
    puts("SAMPLE_CHECKS=PASS");
    return 0;
}
