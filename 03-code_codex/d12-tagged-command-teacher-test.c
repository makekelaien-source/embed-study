/* Teacher harness: left-hand label is intentionally not validated. */
#include <stdio.h>
#include <string.h>
#include "d12-tagged-command.h"
static int failures = 0;
static void check(const char *name, const char *input, int capacity, int expected)
{
    int actual = tagged_command_kind(input, capacity);
    printf("%s: %s (actual=%d expected=%d)\n", name,
           actual == expected ? "PASS" : "FAIL", actual, expected);
    if (actual != expected) failures++;
}
int main(void)
{
    check("run", "CMD/RUN", sizeof "CMD/RUN", 1);
    check("stop", "CMD/STOP", sizeof "CMD/STOP", 2);
    check("empty-field", "CMD/", sizeof "CMD/", 0);
    check("missing-separator", "CMD", sizeof "CMD", -1);
    check("extra-field", "CMD/RUN/EXTRA", sizeof "CMD/RUN/EXTRA", 0);
    check("arbitrary-label", "ROOM/RUN", sizeof "ROOM/RUN", 1);
    check("empty-label", "/STOP", sizeof "/STOP", 2);
    check("empty-input", "", sizeof "", -1);
    check("lowercase", "CMD/run", sizeof "CMD/run", 0);
    check("trailing-space", "CMD/RUN ", sizeof "CMD/RUN ", 0);
    char original[] = "CMD/STOP";
    check("caller-array", original, sizeof original, 2);
    int unchanged = strcmp(original, "CMD/STOP") == 0;
    printf("input-unchanged: %s\n", unchanged ? "PASS" : "FAIL");
    if (!unchanged) failures++;
    printf("FAILURES=%d\n", failures);
    return failures ? 1 : 0;
}
