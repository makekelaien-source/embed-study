#include <stdio.h>
#include "D19-ring-queue.h"

#ifndef CHECK_QUEUE
int main(void)
{
    unsigned int index = 1;
    for (unsigned int i = 0; i < 4; ++i) {
        printf("%u%c", index, i == 3 ? '\n' : ' ');
        index = (index + 1u) % QUEUE_CAPACITY;
    }
    return 0;
}
#else
#define CHECK(expr) do { if (!(expr)) { fprintf(stderr, "failed line %d: %s\n", __LINE__, #expr); return 1; } } while (0)

static int same_state(const struct IntQueue *a, const struct IntQueue *b)
{
    for (unsigned int i = 0; i < QUEUE_CAPACITY; ++i) {
        if (a->slots[i] != b->slots[i]) return 0;
    }
    return a->head == b->head && a->tail == b->tail && a->count == b->count;
}

int main(void)
{
    struct IntQueue q = {0};
    struct IntQueue other = {0};
    struct IntQueue before = q;
    int out = -99;

    CHECK(queue_pop(&q, &out) == QUEUE_EMPTY && out == -99 && same_state(&q, &before));
    CHECK(queue_push(&q, 10) == QUEUE_OK);
    CHECK(queue_push(&q, 20) == QUEUE_OK);
    CHECK(queue_push(&q, 30) == QUEUE_OK);
    CHECK(q.count == 3u && q.head == q.tail);
    before = q;
    CHECK(queue_push(&q, 40) == QUEUE_FULL && same_state(&q, &before));
    CHECK(queue_pop(&q, &out) == QUEUE_OK && out == 10);
    CHECK(queue_push(&q, 40) == QUEUE_OK);
    CHECK(queue_push(&other, 0) == QUEUE_OK);
    CHECK(queue_pop(&q, &out) == QUEUE_OK && out == 20);
    CHECK(queue_pop(&q, &out) == QUEUE_OK && out == 30);
    CHECK(queue_pop(&q, &out) == QUEUE_OK && out == 40);
    CHECK(q.count == 0u && q.head == q.tail);
    before = q;
    CHECK(queue_pop(&q, &out) == QUEUE_EMPTY && out == 40 && same_state(&q, &before));
    CHECK(queue_pop(&other, &out) == QUEUE_OK && out == 0);
    puts("QUEUE_CHECKS=PASS");
    return 0;
}
#endif
