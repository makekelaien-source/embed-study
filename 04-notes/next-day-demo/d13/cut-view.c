#include <stdio.h>
#include <string.h>
int main(void)
{
    char text[]="ZONE/AUTO";
    char *slash=strchr(text,'/');
    char *suffix=slash+1;
    *slash='\0';
    printf("left=%s right=%s left_length=%zu\n",text,suffix,strlen(text));
    return 0;
}
