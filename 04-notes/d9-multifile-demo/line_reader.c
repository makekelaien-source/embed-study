#include <stdio.h>
#include "line_reader.h"

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
    }
    return 2 ;  
}
