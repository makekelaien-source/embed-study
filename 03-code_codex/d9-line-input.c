#include <stdio.h>



int main(void){
    char text [8];
    
    if (fgets(text,sizeof text, stdin) == NULL)
    {
        printf ("READ+FAILED");
        return 0 ;
    }

    printf ("text=[%s]\n",text);
    return 0 ;
    
}