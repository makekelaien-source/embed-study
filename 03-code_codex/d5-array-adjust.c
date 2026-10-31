#include <stdio.h>
#define num 3

void add_each(int *values,int count, int amount){

    for (int i = 0; i < count ; i++)
    {
        values [i] += amount;
        printf ("%d\n",values[i]);
    }
    
    
}

int main(void){
    int samples[num] = {10,20,30};
    int count = 3; int amount = 5;
    add_each (samples,count,amount);
    return 0 ;
}