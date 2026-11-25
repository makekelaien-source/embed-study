#ifndef D19_DYNAMIC_QUEUE_H
#define D19_DYNAMIC_QUEUE_H

#include <stddef.h>

struct DynamicQueue {
    int *slots;
    size_t capacity;
    size_t head;
    size_t tail;
    size_t count;
};

int queue_init(struct DynamicQueue *q, size_t capacity);

void queue_destroy(struct DynamicQueue *q);

int queue_clone(struct DynamicQueue *dst, const struct DynamicQueue *src);

#endif
