#include <stdio.h>
int copy_text(char *desination,int capacity,const char *source);

int text_length(const char *text){
    int i = 0 ;
    while (text [i] != '\0')
    {
        i ++ ;
        
    }return i ;
     
}

int main (void){
    char destination[6] = "OLD";
    char source[] = "HELLO";
    int capacity = sizeof (destination) / sizeof (destination[0]) ;
    if (copy_text(destination,capacity,source) == 1)
    {

        printf("1 %s",destination);
    }
    return 0 ;    
}

int copy_text(char *desination,int capacity, const char *source){
    int length = text_length(source) ;
    if (capacity >= length + 1)
    {
        for (int i = 0; i < length + 1 ; i++)
        {
            desination[i] = source [i];
        }
        return 1 ;
    }return 0;
    
}