#include "queue-device-all.h"

enum QueueResult device_consume_all(struct IntQueue *q, enum DeviceState *state){
    int *b = 1;
    int a = queue_pop(q,&b); int c = 0;
    while (a != QUEUE_EMPTY)
    {
        *state = device_step(*state, b);
        a = queue_pop(q,&b);
        c++;
    }
    if (c == 0 )
    {
        return QUEUE_EMPTY;
    }else return QUEUE_OK;
}