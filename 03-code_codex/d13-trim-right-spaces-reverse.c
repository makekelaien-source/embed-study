#include <stdio.h>
#include <string.h>

void trim_right_spaces(char *text){
    int length = strlen(text) ;
    if (length == 0)
    {
        return;
    }else{
        length -= 1 ;
        while (text [length] == ' ')
        {
            if (length == 0){
                length -= 1 ;
                break;
        }
            length -= 1 ;
        }
        length ++;
        text [length] = '\0';
    }}