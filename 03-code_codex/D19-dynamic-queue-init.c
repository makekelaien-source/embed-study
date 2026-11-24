#include <stdlib.h>
#include "D19-dynamic-queue.h"

int queue_init(struct DynamicQueue *q, size_t capacity){
    if (capacity == 0)
    {
        return 0 ;
    }
    q->slots = malloc(capacity * sizeof *q->slots);
    if (q->slots == NULL)
    {
        return 0 ;
    }
    q->capacity = capacity;
    return 1 ;
}