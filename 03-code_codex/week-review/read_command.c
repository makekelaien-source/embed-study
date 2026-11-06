#include <stdio.h>
#include "review_input.h"

int main(void){
    char dest[8];
    int a = read_text(dest,sizeof dest);
    if (a == -1 )
    {
        return -1 ;
    }else if (a == 0 )
    {
        return 0 ;
    }else if (a == 1 )
    {
        printf ("%s",dest);
    }else if (a == READ_TEXT_NEEDS_TAIL){
        int tail_status = check_tail();
        if (tail_status == CHECK_TAIL_NEWLINE)
        {
            printf ("%s",dest);
        }
    }
    return 0;
}
