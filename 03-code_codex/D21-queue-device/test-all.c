#include "queue-device-all.h"
#include <assert.h>
#include <stdio.h>

static void assert_same_queue(const struct IntQueue *a,
                              const struct IntQueue *b)
{
    assert(a->head == b->head);
    assert(a->tail == b->tail);
    assert(a->count == b->count);
    for (unsigned int i = 0; i < QUEUE_CAPACITY; i++) {
        assert(a->slots[i] == b->slots[i]);
    }
}

static void enqueue(struct IntQueue *q, enum DeviceEvent event)
{
    enum QueueResult result = queue_push(q, event);
    assert(result == QUEUE_OK);
}

int main(void)
{
    struct IntQueue q = {0};
    struct IntQueue other = {0};
    enum DeviceState state = RUN;
    enum DeviceState other_state = BOOT;
    enum QueueResult result;
    struct IntQueue before = q;

    result = device_consume_all(&q, &state);
    assert(result == QUEUE_EMPTY && state == RUN);
    assert_same_queue(&q, &before);

    state = IDLE;
    enqueue(&q, START);
    result = device_consume_all(&q, &state);
    assert(result == QUEUE_OK && state == RUN);
    assert(q.count == 0 && q.head == q.tail);

    state = BOOT;
    enqueue(&q, START);
    enqueue(&q, START);
    result = device_consume_all(&q, &state);
    assert(result == QUEUE_OK && state == BOOT);
    assert(q.count == 0 && q.head == q.tail);

    state = RUN;
    enqueue(&q, FAULT);
    enqueue(&q, RESET);
    enqueue(&q, READY);
    result = device_consume_all(&q, &state);
    assert(result == QUEUE_OK && state == IDLE);
    assert(q.count == 0 && q.head == q.tail);
    enqueue(&q, START);
    result = device_consume_all(&q, &state);
    assert(result == QUEUE_OK && state == RUN && q.count == 0);

    enqueue(&other, READY);
    enqueue(&other, START);
    before = other;
    enqueue(&q, FAULT);
    result = device_consume_all(&q, &state);
    assert(result == QUEUE_OK && state == SAFE && q.count == 0);
    assert(other_state == BOOT);
    assert_same_queue(&other, &before);

    result = device_consume_all(&other, &other_state);
    assert(result == QUEUE_OK && other_state == RUN && other.count == 0);
    assert(state == SAFE);

    before = q;
    result = device_consume_all(&q, &state);
    assert(result == QUEUE_EMPTY && state == SAFE);
    assert_same_queue(&q, &before);

    enqueue(&q, READY);
    enqueue(&q, RESET);
    enqueue(&q, START);
    before = q;
    result = queue_push(&q, FAULT);
    assert(result == QUEUE_FULL);
    assert_same_queue(&q, &before);
    assert(state == SAFE);
    result = device_consume_all(&q, &state);
    assert(result == QUEUE_OK && state == BOOT && q.count == 0);

    puts("QUEUE_DEVICE_ALL_CHECKS=PASS");
    return 0;
}
