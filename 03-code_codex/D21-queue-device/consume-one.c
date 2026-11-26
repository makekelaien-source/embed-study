#include "queue-device.h"

enum QueueResult device_consume_one(struct IntQueue *q, enum DeviceState *state){
    int *out ;
    enum QueueResult situation = queue_pop(state,out);
    while (situation != QUEUE_EMPTY)
    {
        state = device_step(state,q->slots);
        situation = queue_pop(state,out);
    }
    return state ;
    
}