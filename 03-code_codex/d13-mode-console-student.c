#include <stdio.h>
#include "d13-mode-command.h"

int main(void){
    char text [16] ;
    char *a = fgets(text,sizeof text,stdin);
    if (a == NULL)
    {
        return -5;
    }else{
        return classify_mode(text,sizeof text);
    }
    
}