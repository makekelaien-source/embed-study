#include <stdio.h>
#include "classify.h"

int main(void)
{
    printf("RUN=%d STOP=%d BAD=%d\n",
           classify_command("RUN"),
           classify_command("STOP"),
           classify_command("run"));
    return 0;
}