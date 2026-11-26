#include "queue-device.h"
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

    result = device_consume_one(&q, &state);
    assert(result == QUEUE_EMPTY);
    assert(state == RUN);
    assert_same_queue(&q, &before);

    state = IDLE;
    enqueue(&q, START);
    assert(state == IDLE);
    result = device_consume_one(&q, &state);
    assert(result == QUEUE_OK);
    assert(state == RUN);
    assert(q.count == 0 && q.head == 1 && q.tail == 1);

    state = BOOT;
    enqueue(&q, START);
    result = device_consume_one(&q, &state);
    assert(result == QUEUE_OK);
    assert(state == BOOT);
    assert(q.count == 0 && q.head == 2 && q.tail == 2);

    state = RUN;
    enqueue(&q, FAULT);
    enqueue(&q, RESET);
    enqueue(&q, READY);
    before = q;
    result = queue_push(&q, START);
    assert(result == QUEUE_FULL);
    assert(state == RUN);
    assert_same_queue(&q, &before);

    result = device_consume_one(&q, &state);
    assert(result == QUEUE_OK);
    assert(state == SAFE);
    assert(q.count == 2 && q.head == 0 && q.tail == 2);
    assert(q.slots[q.head] == RESET);

    before = q;
    enqueue(&other, READY);
    result = device_consume_one(&other, &other_state);
    assert(result == QUEUE_OK && other_state == IDLE && other.count == 0);
    assert(state == SAFE);
    assert_same_queue(&q, &before);

    result = device_consume_one(&q, &state);
    assert(result == QUEUE_OK);
    assert(state == BOOT);
    assert(q.count == 1 && q.head == 1 && q.tail == 2);
    assert(q.slots[q.head] == READY);

    result = device_consume_one(&q, &state);
    assert(result == QUEUE_OK);
    assert(state == IDLE);
    assert(q.count == 0 && q.head == 2 && q.tail == 2);

    before = q;
    result = device_consume_one(&q, &state);
    assert(result == QUEUE_EMPTY && state == IDLE);
    assert_same_queue(&q, &before);

    puts("QUEUE_DEVICE_CHECKS=PASS");
    return 0;
}
