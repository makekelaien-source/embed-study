/* Teacher probe: uses the preserved command library, not a new parsing layer. */
#include <stdio.h>
#include "shared-command/d12-line-reader.h"
#include "shared-command/d12-bounded-command.h"
int main(void)
{
    char text[16];
    int status=read_complete_line(text,sizeof text);
    printf("read=%d\n",status);
    if(status==LINE_READY) {
        int kind=bounded_command_kind(text,sizeof text);
        printf("text=[%s] kind=%d\n",text,kind);
    }
    return 0;
}
