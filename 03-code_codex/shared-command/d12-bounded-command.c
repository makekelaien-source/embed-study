#include <stddef.h>
#include "shared-text/d11-token-prefix.h"
#include "d12-strict-command.h"

int bounded_command_kind(const char *text, int capacity){
    if (text == NULL || capacity < 0 || capacity == token_prefix_length(text,capacity,'\0'))
    {
        return -4 ;
    }else return strict_command_kind(text,capacity);   
}