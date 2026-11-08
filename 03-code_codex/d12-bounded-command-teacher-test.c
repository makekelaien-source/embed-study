/* Teacher harness: buffers need not initially contain a terminator. */
#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include "d12-bounded-command.h"
static int failures=0;
static void check(const char *name, const char *text, int capacity, int expected)
{
    int actual=bounded_command_kind(text,capacity);
    printf("%s: %s (actual=%d expected=%d)\n",name,
           actual==expected ? "PASS":"FAIL",actual,expected);
    if(actual!=expected) failures++;
}
int main(void)
{
    check("null-positive",NULL,8,-4);
    check("null-zero",NULL,0,-4);
    check("zero-range","CMD/RUN",0,-4);
    check("negative-range","CMD/RUN",-1,-4);
    char raw[]={'C','M','D','/','R','U','N'};
    check("unterminated",raw,sizeof raw,-4);
    check("terminator-outside-range","CMD/RUN",7,-4);
    check("terminator-at-last-slot","CMD/RUN",8,1);
    check("only-prefix-in-range","CMD/RUN",4,-4);
    char padded[12]={'C','M','D','/','R','U','N','\0','X','Y','Z','W'};
    check("terminator-before-buffer-end",padded,sizeof padded,1);
    char nul_only[]={'\0'};
    check("empty-string",nul_only,sizeof nul_only,-1);
    char one_raw[]={'C'};
    check("single-unterminated",one_raw,sizeof one_raw,-4);
    check("missing-separator","CMD",sizeof "CMD",-1);
    check("empty-field","CMD/",sizeof "CMD/",-2);
    check("wrong-label","ROOM/RUN",sizeof "ROOM/RUN",-3);
    check("wrong-label-empty-field","ROOM/",sizeof "ROOM/",-3);
    check("unknown-command","CMD/JUMP",sizeof "CMD/JUMP",0);
    check("stop","CMD/STOP",sizeof "CMD/STOP",2);
    check("extra-field","CMD/RUN/EXTRA",sizeof "CMD/RUN/EXTRA",0);
    char invalid_label_raw[]={'X','/'};
    check("unterminated-before-label",invalid_label_raw,sizeof invalid_label_raw,-4);
    char a[]="CMD/STOP";
    check("caller-array",a,sizeof a,2);
    int unchanged=strcmp(a,"CMD/STOP")==0 && memcmp(raw,"CMD/RUN",sizeof raw)==0;
    printf("inputs-unchanged: %s\n",unchanged ? "PASS":"FAIL");
    if(!unchanged) failures++;
    printf("FAILURES=%d\n",failures);
    return failures ? 1:0;
}
