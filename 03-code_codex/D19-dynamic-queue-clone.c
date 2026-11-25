#include "D19-dynamic-queue.h"
#include <stdio.h>

int queue_clone(struct DynamicQueue *dst, const struct DynamicQueue *src){
    int d = dst->head;int s = src->head ;
    int num = src->count; 
    if (queue_init(dst,src->capacity) == 0){
        return 0;
    }else{
        while (num != 0)
        {
            dst->slots[d] = src->slots[s];
            d = (d+1) % src->capacity; s = (s+1) % src->capacity;
            num --;
            dst->count ++;
            dst->tail = (dst->tail + 1) % src->capacity;
        }
        return 1;
    }
}