#include <stdio.h>
#include <string.h>

void trim_right_spaces(char *text){
    const char *p = strchr(text,' ');
    int a = strlen(text);
    int length = 0;
    if (a <= 99 && a != 0)
    {
        if (p == NULL)
        {return ;
        }else{
            while (*(p + 1) != ' ' && *(p + 1) != '\0')
            {
                p ++ ;
                p = strchr(p,' ');
            }
            while(*(p + 1) == ' ')
            {
                p = p + 1 ;
                length ++;
                }  
            if ( *p == '\0' ){
                char *b = text [p - length - text ];
            }
    }
}}