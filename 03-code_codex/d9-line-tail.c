#include <stdio.h>

int check_tail(void){
    int a = fgetc(stdin);
    if (a == '\n')
    {
        return 1 ;
    }else if (a == EOF)
    {
        return 0 ;
    }else {
        while (a != '\n' && a != EOF)
        {
            a = fgetc(stdin);
        }
        
    }return 2 ;
}