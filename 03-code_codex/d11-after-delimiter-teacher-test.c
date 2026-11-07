/* Teacher harness: identity checks confirm borrowed addresses. */
#include <stdio.h>
#include <stddef.h>
#include "d11-after-delimiter.h"
static int failures = 0;
static void check(const char *name, const char *text, int capacity, char delimiter, const char *expected)
{
    const char *actual = after_delimiter(text, capacity, delimiter);
    int ok = actual == expected;
    printf("%s %s actual=", name, ok ? "PASS" : "FAIL");
    if (actual == NULL) printf("NULL");
    else printf("[%s]", actual);
    printf(" expected=");
    if (expected == NULL) printf("NULL\n");
    else printf("[%s]\n", expected);
    if (!ok) failures++;
}
int main(void)
{
    char run_auto[]="RUN AUTO";
    char trailing[]="RUN ";
    char leading[]="/GO";
    char nested[]="A/B/C";
    char no_separator[]="RUN";
    char go[]="GO";
    check("normal",run_auto,9,' ',run_auto+4);
    check("empty-suffix",trailing,5,' ',trailing+4);
    check("leading-separator",leading,4,'/',leading+1);
    check("first-separator",nested,6,'/',nested+2);
    check("no-separator",no_separator,4,' ',NULL);
    check("zero-capacity",NULL,0,'/',NULL);
    check("nul-delimiter",go,3,'\0',NULL);
    printf("FAILURES=%d\n",failures);
    return failures ? 1 : 0;
}
