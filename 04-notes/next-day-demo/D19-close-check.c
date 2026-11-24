#include <assert.h>
#include <stdio.h>
#include "D19-ring-queue.h"
#include "D19-dynamic-queue.h"

int queue_equal(const struct IntQueue *a, const struct IntQueue *b);

static void check_fixed_queue(void)
{
    struct IntQueue a = {0};
    struct IntQueue b = {0};
    int out = -1;
    assert(queue_push(&a, 10) == QUEUE_OK);
    assert(queue_push(&a, 20) == QUEUE_OK);
    assert(queue_push(&b, 99) == QUEUE_OK);
    assert(queue_push(&b, 88) == QUEUE_OK);
    assert(queue_pop(&b, &out) == QUEUE_OK && out == 99);
    assert(queue_pop(&b, &out) == QUEUE_OK && out == 88);
    assert(queue_push(&b, 10) == QUEUE_OK);
    assert(queue_push(&b, 20) == QUEUE_OK);
    assert(b.head == 2 && b.tail == 1);
    assert(queue_equal(&a, &b) == 1);
    assert(queue_pop(&b, &out) == QUEUE_OK && out == 10);
    assert(queue_equal(&a, &b) == 0);
    assert(queue_pop(&b, &out) == QUEUE_OK && out == 20);
    assert(queue_pop(&b, &out) == QUEUE_EMPTY && out == 20);
}

static void check_dynamic_snapshot(void)
{
    struct DynamicQueue source = {0};
    struct DynamicQueue copy = {0};
    assert(queue_init(&source, 0) == 0 && source.slots == NULL);
    assert(queue_init(&source, 3) == 1);
    source.head = 2;
    source.tail = 1;
    source.count = 2;
    source.slots[2] = 10;
    source.slots[0] = 20;
    assert(queue_clone(&copy, &source) == 1);
    assert(copy.slots != source.slots && copy.capacity == 3);
    assert(copy.count == 2 && copy.head == 0 && copy.tail == 2);
    source.slots[2] = -1;
    queue_destroy(&source);
    assert(source.slots == NULL && source.count == 0 && source.capacity == 0);
    assert(source.head == 0 && source.tail == 0);
    assert(copy.slots[0] == 10 && copy.slots[1] == 20);
    queue_destroy(&source);
    queue_destroy(&copy);
    assert(copy.slots == NULL);
}

int main(void)
{
    check_fixed_queue();
    check_dynamic_snapshot();
    puts("D19_CLOSE_CHECKS=PASS");
    return 0;
}
