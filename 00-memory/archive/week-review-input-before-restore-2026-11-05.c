#include <stdio.h>
#include "review_input.h"

/* Teacher copy of your D9 read_text and check_tail. */
int read_text(char *dest, int capacity){
    if (capacity < 2)
    {
        return -1 ;
    }
    if (fgets(dest,capacity,stdin) == NULL)
    {
        return 0 ;
    }
    for (int i = 0; i < capacity; i++)
    {
        if (dest[i] == '\n')
        {
            dest[i] = '\0';
            return 1 ;
        }
        else if (dest[i] == '\0')
    {
        return 2 ;  
    }
        else if ( dest[i] != '\n' && dest[i] == '\0'){
            return 3 ;
        } 
    }
    
}

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
