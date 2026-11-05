#include <stdio.h>
#include "review_input.h"

int main(void){
    char dest[8];
    int a = read_text(dest,sizeof dest);
    while (a == 2)
    {
        if (check_tail() == 1 ){
        a = read_text(dest,sizeof dest);
    }}
    if (a == 1)
    {
        printf ("%s",dest);
    }
    return 0;
}