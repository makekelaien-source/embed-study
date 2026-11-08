#include <stdio.h>
#include <string.h>

int comparison_count(const char *left, const char *right){
    int length = 0 ;

    for (int i = 0 ;;i++){
        length ++ ;
        if (left[i] == right [i] && left[i] != '\0'){
        }else if (left[i] != right [i] || left[i] == '\0' || right [i] == '\0')
        {
            return length ;
        }
    } 
}