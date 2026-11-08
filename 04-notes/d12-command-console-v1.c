#include <stdio.h>
#include "d12-line-reader.h"
#include "d12-bounded-command.h"

int main(void){
    char text[16];
    int capacity = sizeof text ;
    int ch = fgets(text,capacity,stdin);
    int a ;
    while (ch != NULL)
    {
        a = read_complete_line(text, capacity);
        if (a == LINE_READY)
        {
            int b = bounded_command_kind(text,capacity);
            printf ("%d\n",b);
            ch = fgets(text,capacity,stdin);
            continue;
        }else if (a == LINE_END)
        {
            return 0;
        }else if (a == LINE_TOO_LONG)
        {
            puts("TOO_LONG");
            ch = fgets(text,capacity,stdin);
            continue;
        }else if (a == LINE_IO_ERROR)
        {
            puts ("READ_ERROR");
            return 1;
        }else if (a == LINE_BAD_BUFFER)
        {
            puts ("BUFFER_ERROR");
            return 1;
        }    
    }
    return 0;
}