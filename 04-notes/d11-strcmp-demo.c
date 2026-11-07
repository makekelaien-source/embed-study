#include <stdio.h>
#include <string.h>

int main(void)
{
    char first[]="RUN";
    char second[]="RUN";
    const char *left=first;
    const char *right=second;
    printf("address_same=%d content_same=%d\n",left==right,strcmp(left,right)==0);
    printf("same=%d\n",strcmp("RUN","RUN"));
    int result=strcmp("RUN","RUN AUTO");
    printf("prefix-result=%s\n",result<0 ? "NEGATIVE" : result>0 ? "POSITIVE" : "ZERO");
    return 0;
}
