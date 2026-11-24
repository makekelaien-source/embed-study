#include "D19-ring-queue.h"

enum QueueResult queue_push(struct IntQueue *q, int value){
    if (q->count < QUEUE_CAPACITY)
    {
        q->slots[q->tail] = value;
        return QUEUE_OK;
    }
    return QUEUE_FULL ;
}