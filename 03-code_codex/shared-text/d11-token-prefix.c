#include "d11-token-prefix.h"
#include "d11-after-delimiter.h"
#include <stddef.h>
#include <stdio.h>

int token_prefix_length(const char *text, int capacity, char delimiter){
    {
    int a = 0;
    for (int i = 0; i < capacity; i++)
    {
        if (text == NULL || text [i] == delimiter || text[i] == '\0')
        {
            return a;
        }else a ++;
    }
    return a ;
    }
}
