#include <stdio.h>
int is_hot(int temperature);

int main (void){
    printf ("%d\n",is_hot(29));
    printf ("%d\n",is_hot(30));
    return 0 ;
}

int is_hot(int temperature){
    if (temperature >= 30)
    {
        return 1 ;
    }else
        return 0 ;
}