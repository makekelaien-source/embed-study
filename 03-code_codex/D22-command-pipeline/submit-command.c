#include "submit-command.h"

enum SubmitResult submit_command(struct IntQueue *q, const char *text){
    int a = command_kind(text);
    if (a == -1 || a == 0)
    {
        return SUBMIT_INVALID;
    }else{
        if (q ->count == QUEUE_CAPACITY)
        {
            return SUBMIT_FULL;
        }else if (a == 1)
        {
            queue_push(q,START);
        }else if (a ==2)
        {
            queue_push(q,STOP);
        }
        return SUBMIT_OK;
    }
    
}