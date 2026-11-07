/* Teacher test harness; student implementation remains unchanged. */
#include <stdio.h>
#include <stddef.h>
#include "d11-token-prefix.h"
#include "d11-token-prefix.h"

static int failures = 0;
static void check(const char *name, const char *text, int capacity, int expected)
{
    int actual = token_prefix_length(text, capacity, ' ');
    printf("%s: expected=%d actual=%d %s\n", name, expected, actual,
           actual == expected ? "PASS" : "FAIL");
    if (actual != expected) failures++;
}
static void check_delimited(const char *name, const char *text, int capacity, char delimiter, int expected)
{
    int actual = token_prefix_length(text, capacity, delimiter);
    printf("%s: expected=%d actual=%d %s\n", name, expected, actual,
           actual == expected ? "PASS" : "FAIL");
    if (actual != expected) failures++;
}

int main(void)
{
    const char fragment[3] = {'A', 'B', 'C'};
    const char embedded[5] = {'A', '\0', 'B', 'C', 'D'};
    char writable[4] = {'A', 'B', ' ', 'C'};
    check("space-separated", "RUN AUTO", 8, 3);
    check("leading-space", " RUN", 4, 0);
    check("string-terminator", "GO", 3, 2);
    check("unterminated-fragment", fragment, 3, 3);
    check("range-before-space", "AB CD", 2, 2);
    check("empty-string", "", 1, 0);
    check("null-zero-range", NULL, 0, 0);
    check("nonnull-zero-range", "GO", 0, 0);
    check("one-character-range", fragment, 1, 1);
    check("one-space-range", " ", 1, 0);
    check("nul-before-tail", embedded, 5, 1);
    check("space-at-last-readable", "AB ", 3, 2);
    check("newline-is-ordinary", "A\nB", 4, 3);
    check("tab-is-ordinary", "A\tB", 4, 3);
    check("string-longer-than-range", "ABCDEFG", 4, 4);
    check("writable-input", writable, 4, 2);
    if (writable[0]!='A' || writable[1]!='B' || writable[2]!=' ' || writable[3]!='C') failures++;
    const char pipe_fragment[3] = {'A', '|', 'B'};
    check_delimited("slash-separator", "RUN/AUTO", 9, '/', 3);
    check_delimited("slash-not-selected", "RUN/AUTO", 9, ' ', 8);
    check_delimited("pipe-fragment", pipe_fragment, 3, '|', 1);
    check_delimited("nul-delimiter", "GO", 3, '\0', 2);
    check_delimited("newline-delimiter", "A\nB", 4, '\n', 1);
    check_delimited("tab-delimiter", "A\tB", 4, '\t', 1);
    check_delimited("delimiter-first", "/GO", 4, '/', 0);
    check_delimited("range-before-slash", "AB/CD", 2, '/', 2);
    check_delimited("fragment-nul-delimiter", fragment, 3, '\0', 3);
    check_delimited("null-zero-new-delimiter", NULL, 0, '/', 0);
    printf("FAILURES=%d\n", failures);
    return failures ? 1 : 0;
}
