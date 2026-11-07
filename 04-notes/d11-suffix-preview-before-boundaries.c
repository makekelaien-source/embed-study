#include <stdio.h>
#include "d11-after-delimiter.h"

int main(void){
    char text[] = "RUN AUTO";
    int ch = fgetc(stdin);
    if (ch == EOF)
    {
        return 0 ;
    }
    
    const char *a = after_delimiter(text,sizeof text ,ch) ;
    if (a == NULL)
    {
        puts ("NO_SUFFIX");
    }else{
        printf ("%s",a);
        text[a - text] = 'X';
        printf ("%s",a);
    }
    return 0;

}

char text[] = "HOLEFUL"
const char *p = text ;
*p = text + 1;