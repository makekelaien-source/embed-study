#include <stdio.h>
#include "d11-token-prefix.h"

int main(void){
    char text[] = "RUN AUTO";
    int delimter = fgetc(stdin);
    if (delimter == EOF)
    {
        return 0 ;
    }else {
        int a = token_prefix_length(text,sizeof text,delimter);
        printf ("%d",a);
        return 0;
    }
    
}