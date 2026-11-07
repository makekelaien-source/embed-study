#include <stdio.h>
#include "d11-after-delimiter.h"

const char *after_delimiter(const char *text, int capacity, char delimiter){
    int a = token_prefix_length(text,capacity,delimiter); /*在delimiter\结束符之前的文本量*/
    if (capacity == 0 || delimiter == '\0' || text [a] == '\0'){
        return NULL;}
    else{ 
    return text + a + 1 ;}
}
