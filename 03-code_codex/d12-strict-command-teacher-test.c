/* Teacher v3 harness: missing separator takes precedence over label validation. */
#include <stdio.h>
#include <string.h>
#include "d12-strict-command.h"
static int failures = 0;
static void check(const char *name, const char *text, int capacity, int expected)
{
    int actual = strict_command_kind(text, capacity);
    printf("%s: %s (actual=%d expected=%d)\n", name,
           actual == expected ? "PASS" : "FAIL", actual, expected);
    if (actual != expected) failures++;
}
int main(void)
{
    check("run", "CMD/RUN", sizeof "CMD/RUN", 1);
    check("stop", "CMD/STOP", sizeof "CMD/STOP", 2);
    check("missing", "CMD", sizeof "CMD", -1);
    check("missing-wrong-label", "ROOM", sizeof "ROOM", -1);
    check("empty-input", "", sizeof "", -1);
    check("empty-field", "CMD/", sizeof "CMD/", -2);
    check("wrong-label", "ROOM/RUN", sizeof "ROOM/RUN", -3);
    check("long-label", "CMDX/RUN", sizeof "CMDX/RUN", -3);
    check("empty-label", "/STOP", sizeof "/STOP", -3);
    check("lowercase-label", "cmd/RUN", sizeof "cmd/RUN", -3);
    check("wrong-label-empty-field", "ROOM/", sizeof "ROOM/", -3);
    check("separator-only", "/", sizeof "/", -3);
    check("label-space", "CMD /RUN", sizeof "CMD /RUN", -3);
    check("unknown-command", "CMD/JUMP", sizeof "CMD/JUMP", 0);
    check("lowercase-command", "CMD/run", sizeof "CMD/run", 0);
    check("trailing-space", "CMD/RUN ", sizeof "CMD/RUN ", 0);
    check("extra-field", "CMD/RUN/EXTRA", sizeof "CMD/RUN/EXTRA", 0);
    check("space-field", "CMD/ ", sizeof "CMD/ ", 0);
    char text[]="CMD/STOP";
    check("caller-array", text, sizeof text, 2);
    int unchanged=strcmp(text, "CMD/STOP")==0;
    printf("input-unchanged: %s\n", unchanged ? "PASS" : "FAIL");
    if (!unchanged) failures++;
    printf("FAILURES=%d\n", failures);
    return failures ? 1 : 0;
}
