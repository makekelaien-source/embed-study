#include <stdio.h>
int main(void){
    int a = 5 ;
    if (scanf ("%d",&a) == 1)
    {
        printf ("INPUT_OK %d\n",a);
        return 0 ;
    }else {
        printf ("INPUT_ERROR\n");
        return 1 ;
    }
    
}