#include <stdio.h>
#include "d10-command-policy.h"

int command_is_usable(int status, const char *text, int eof_confirmed){
    if (status == COMMAND_COMPLETE)
    {
        {
            if ( text [0] != '\0')
        {
            return 1 ; /*状态为正常结束，不为空返回1，为空返回0*/
        }else return 0 ;
        }   
    }
    
    if (status == COMMAND_END_UNCONFIRMED)
    {
        if (eof_confirmed == 1 && text [0] != '\0')
        {
            return 1 ;/*状态为不确定，如果正常结束并且不为空返回1，其他情况返回2*/
        }else return 0 ;    
    }
        return 0 ;

}