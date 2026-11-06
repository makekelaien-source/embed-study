#include <stdio.h>
#include "d10-read-status.h"

int classify_read(int ch, int end_flag, int error_flag){
    if (ch != EOF)
    {
        
        return D10_READ_CHAR;
    } 
    else { if (error_flag != 0)
        {
            return D10_READ_ERROR ;}
        else if (end_flag != 0){
        
            return D10_READ_END;
        
        }else return D10_READ_UNKNOWN ; }
}
