#include <stdlib.h>
#include "D19-dynamic-queue.h"

int queue_init(struct DynamicQueue *q, size_t capacity){
    *q->slots = malloc(capacity * sizeof *q->slots);
    if (q->slots == 0 || q->slots == NULL)
    {
        return 0 ;
    }
    return 1 ;
}