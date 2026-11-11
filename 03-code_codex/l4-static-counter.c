#include <stdio.h>
int record_event(int reset);

int record_event(int reset){
    static int number = 0;
    if (reset == 1)
    {
        number = 0 ;
    }else number ++;
    return number;
}