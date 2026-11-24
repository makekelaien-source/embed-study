#ifndef D19_RING_QUEUE_H
#define D19_RING_QUEUE_H

enum { QUEUE_CAPACITY = 3 };
enum QueueResult { QUEUE_OK, QUEUE_FULL, QUEUE_EMPTY };

struct IntQueue {
    int slots[QUEUE_CAPACITY];
    unsigned int head;
    unsigned int tail;
    unsigned int count;
};

enum QueueResult queue_push(struct IntQueue *q, int value);
enum QueueResult queue_pop(struct IntQueue *q, int *out);

#endif
