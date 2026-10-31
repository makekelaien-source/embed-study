#include <stdio.h>

int main(void){
    char label [6];
    int words = scanf ("%5s",label);
    if (words == 1)
    {
        printf("%s\n",label);
        label [0] = 'X' ;
        printf("%s",label);
    }else {
        printf ("INPUT_ERROR");
        return 1 ;
    }
    char happy[2];
    scanf("%s",happy);
    printf("%s",happy);
    return 0 ;
    


}