/* Teacher-owned harness; student implements command_kind only. */
#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include "d12-command-kind.h"
static int failures = 0;
static void check(const char *name, const char *input, int expected)
{
    int actual = command_kind(input);
    printf("%s: %s (actual=%d expected=%d)\n", name,
           actual == expected ? "PASS" : "FAIL", actual, expected);
    if (actual != expected) failures++;
}
int main(void)
{
    check("run", "RUN", 1);
    check("stop", "STOP", 2);
    check("empty", "", 0);
    check("trailing-space", "RUN ", 0);
    check("lowercase", "run", 0);
    check("extra-field", "RUN AUTO", 0);
    check("missing", NULL, -1);
    check("prefix", "RU", 0);
    char mutable[] = "STOP";
    check("caller-array", mutable, 2);
    int unchanged = strcmp(mutable, "STOP") == 0;
    printf("input-unchanged: %s\n", unchanged ? "PASS" : "FAIL");
    if (!unchanged) failures++;
    printf("FAILURES=%d\n", failures);
    return failures ? 1 : 0;
}
