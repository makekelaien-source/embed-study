#include <stdio.h>
#include <string.h>
int main(void)
{
    const char *text="ROOM/AUTO";
    const char *found=strchr(text,'/');
    printf("length=%zu suffix=%s\n",strlen(text),found+1);
    printf("missing=%d end=%d empty=%zu\n",strchr(text,'#')==NULL,strchr(text,'\0')==text+9,strlen(""));
    return 0;
}
