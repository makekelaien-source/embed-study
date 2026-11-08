/* Teacher test harness for the explicit pair-by-pair model. */
#include <stdio.h>
#include <string.h>
#include "d12-comparison-count.h"
static int failures = 0;
static void check(const char *name, const char *left, const char *right, int expected)
{
    int actual = comparison_count(left, right);
    printf("%s: %s (actual=%d expected=%d)\n", name,
           actual == expected ? "PASS" : "FAIL", actual, expected);
    if (actual != expected) failures++;
}
int main(void)
{
    check("equal", "RUN", "RUN", 4);
    check("first-difference", "RUN", "STOP", 1);
    check("third-difference", "ABC", "ABXYZ", 3);
    check("left-prefix", "RUN", "RUN AUTO", 4);
    check("right-prefix", "RUN AUTO", "RUN", 4);
    check("late-difference", "RUN AUTO", "RUN AX", 6);
    check("both-empty", "", "", 1);
    check("left-empty", "", "RUN", 1);
    check("right-empty", "RUN", "", 1);
    check("one-equal", "A", "A", 2);
    check("space-mismatch", "RUN ", "RUN", 4);
    char left[101], right[101];
    for (int i=0; i<100; i++) { left[i]='A'; right[i]='A'; }
    left[100]='\0'; right[100]='\0';
    check("maximum-equal", left, right, 101);
    right[99]='B';
    check("maximum-last-difference", left, right, 100);
    char a[]="ABC", b[]="ABXYZ";
    check("mutable-arrays", a, b, 3);
    int unchanged=strcmp(a,"ABC")==0 && strcmp(b,"ABXYZ")==0;
    printf("inputs-unchanged: %s\n", unchanged ? "PASS" : "FAIL");
    if (!unchanged) failures++;
    printf("FAILURES=%d\n", failures);
    return failures ? 1 : 0;
}
