#include <stdio.h>
#include "line_reader.h"

int main(void){
    char data[8];
    int capacity = sizeof data / sizeof data [0];
    int status = read_text(data,capacity);
    if (status != -1 && status != 0)
    {
        printf ("%s",data);
    }
    
    return 0 ;

}
