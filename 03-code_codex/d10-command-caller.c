#include <stdio.h>
#include "d10-command-policy.h"
int state(int *text,int capacity, int *eof_condirmed);

int main(void){
    char text [8];
    fgets (text,sizeof (text),stdin);
    int confirmed ;
    for (int i = 0; i < sizeof (text); i++)
    {
        if (text[i])
        {
            /* code */
        }
        
    }
    
}