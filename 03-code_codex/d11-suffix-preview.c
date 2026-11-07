#include <stdio.h>
#include "d11-after-delimiter.h"

int main(void){
    char text[] = "RUN AUTO";
    int ch = fgetc(stdin);
    /* Reuse the EOF check from your earlier working input caller. */
    if (ch == EOF)
    {
        return 0;
    }
    const char *a = after_delimiter(text,sizeof text ,ch) ;
    if (a == NULL)
    {
        puts ("NO_SUFFIX");
    }else{
        printf ("%s",a);
        if (a[0] != '\0')
        {
            text[a - text] = 'X';
            printf ("%s",a);
        }
    }
    return 0;

}

/* Pointer experiment notes, kept here without affecting the caller build:
char text[] = "HOLEFUL"
const char *p = text ;
*/