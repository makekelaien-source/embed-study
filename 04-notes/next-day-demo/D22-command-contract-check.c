#include "d12-command-kind.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
    int result;

    result = command_kind(NULL);
    assert(result == -1);
    result = command_kind("RUN");
    assert(result == 1);
    result = command_kind("STOP");
    assert(result == 2);
    result = command_kind("RUNx");
    assert(result == 0);
    result = command_kind("");
    assert(result == 0);

    puts("D22_COMMAND_CONTRACT_CHECKS=PASS");
    return 0;
}
