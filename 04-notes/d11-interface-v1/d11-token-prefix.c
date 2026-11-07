#include "d11-token-prefix.h"
#include <stddef.h>

int token_prefix_length(const char *text, int capacity){
    {
        /* code */
    }
    
    int a = 0;
    for (int i = 0; i < capacity; i++)
    {
        if (text [i] == ' ' || text[i] == '\0' || text == NULL)
        {
            return a;
        }else a ++;
        
    }
    return a ;
    
}
