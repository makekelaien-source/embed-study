/* Teacher harness: identity checks confirm borrowed addresses. */
#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include "d11-after-delimiter.h"
static int failures = 0;
static void check(const char *name, const char *text, int capacity, char delimiter, const char *expected)
{
    const char *actual = after_delimiter(text, capacity, delimiter);
    int ok = actual == expected;
    printf("%s %s actual=", name, ok ? "PASS" : "FAIL");
    if (actual == NULL) printf("NULL");
    else printf("nonNULL");
    printf(" expected=");
    if (expected == NULL) printf("NULL\n");
    else printf("nonNULL\n");
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
    char empty[]="";
    char just_separator[]="/";
    char repeated[]="A//B";
    char newline[]="A\nB";
    char one[]="A";
    char padded[8]={'A','/','B','\0','X','X','X','X'};
    char padded_before[8]={'A','/','B','\0','X','X','X','X'};
    check("empty-source",empty,1,'/',NULL);
    check("only-separator",just_separator,2,'/',just_separator+1);
    check("repeated-separator",repeated,5,'/',repeated+2);
    check("newline-separator",newline,4,'\n',newline+2);
    check("one-no-separator",one,2,'/',NULL);
    check("zero-nonnull",go,0,'/',NULL);
    check("padded-source",padded,8,'/',padded+2);
    int unchanged = memcmp(run_auto,"RUN AUTO",sizeof run_auto)==0 && memcmp(padded,padded_before,sizeof padded)==0;
    printf("source-unchanged %s\n",unchanged ? "PASS":"FAIL");
    if (!unchanged) failures++;
    const char *borrowed=after_delimiter(run_auto,9,' ');
    run_auto[4]='X';
    int alias_ok=borrowed==run_auto+4;
    if (alias_ok) alias_ok=borrowed[0]=='X';
    printf("borrowed-view-sees-change %s\n",alias_ok ? "PASS":"FAIL");
    if (!alias_ok) failures++;
    printf("FAILURES=%d\n",failures);
    return failures ? 1 : 0;
}
