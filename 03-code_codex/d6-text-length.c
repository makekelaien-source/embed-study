#include <stdio.h>

int text_length(const char *text){
    int i = 0 ;
    while (text [i] != '\0')
    {
        i ++ ;
        
    }return i ;
     
}

int main(void){
    char text [100];
    if (scanf("%99s",text) == 1 )
    {
        printf ("%d",text_length(text));
    }
    return 0 ;
    
    
}
