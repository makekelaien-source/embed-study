#include <stdio.h>
#include <string.h>
int main(void)
{
    printf("%d %d %d\n", strcmp("RUN","RUN")==0, strcmp("RUN ","RUN")==0, strcmp("run","RUN")==0);
    int result=strcmp("RUN","RUN AUTO");
    printf("prefix_negative=%d\n",result<0);
    return 0;
}
