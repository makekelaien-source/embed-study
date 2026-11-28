#include "submit-command.h"
#include <assert.h>
#include <stdio.h>
int main(void)
{
    struct IntQueue q = {0};
    enum SubmitResult result = submit_command(&q, "RUNx");
    printf("result=%d count=%u\n", result, q.count);
    fflush(stdout);
    assert(result == SUBMIT_INVALID);
    assert(q.count == 0);
    return 0;
}
