/* Teacher probe for reader only; not the student's console solution. */
#include <stdio.h>
#include <stddef.h>
#include "d12-line-reader.h"
int main(int argc, char **argv)
{
    char text[16];
    if (argc > 1) {
        if (freopen(argv[1],"w",stdin) == NULL) return 3;
        printf("READ=%d\n",read_complete_line(text,sizeof text));
        return 0;
    }
    printf("BAD_NULL=%d BAD_SMALL=%d\n",read_complete_line(NULL,16),read_complete_line(text,1));
    for (;;) {
        int status=read_complete_line(text,sizeof text);
        printf("READ=%d",status);
        if (status==LINE_READY) printf(" TEXT=[%s]",text);
        printf("\n");
        if (status==LINE_END || status<0) return 0;
    }
}
