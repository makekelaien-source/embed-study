#include <stdio.h>
#include <string.h>

int comparison_count(const char *left, const char *right){
    int length = 0 ;
    if (strcmp (left , right) <= 0)
    {
        for (int i = 0; i < sizeof left ; i++)
        {
            length ++ ;
            if (left[i] == right [i] && left[i] != '\0'){
            }else if (left[i] != right [i] || left[i] == '\0')
            {
                return length ;
            }
        }
    }else{
        for (int i = 0; i < sizeof right ; i++)
        {
            length ++ ;
            if (left[i] == right [i] && right[i] != '\0'){
            }else if (left[i] != right [i] || right[i] == '\0')
            {
                return length ;
            }
        }
    }
    
}