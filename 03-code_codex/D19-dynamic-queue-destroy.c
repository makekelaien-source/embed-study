#include <stdlib.h>
#include "D19-dynamic-queue.h"

void queue_destroy(struct DynamicQueue *q){
    q->capacity = 0; q->count = 0; q->head = 0; q->tail = 0 ;
    free(q->slots);
    q->slots = NULL ;
}