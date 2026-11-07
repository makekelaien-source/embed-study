#include <stdio.h>
#include <string.h>
#include "d11-after-delimiter.h"
int main(void)
{
    char line[]="CMD/RUN";
    const char *command=after_delimiter(line,sizeof line,'/');
    if(command==NULL){puts("NO_FIELD");return 0;}
    printf("field=%s equal_RUN=%d\n",command,strcmp(command,"RUN")==0);
    line[4]='X';
    printf("changed=%s\n",command);
    return 0;
}
