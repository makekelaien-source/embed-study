#include "submit-command.h"
#include <assert.h>
#include <stddef.h>
#include <stdio.h>

static void expect_rejection(struct IntQueue *q, const char *text,
                             enum SubmitResult result)
{
    struct IntQueue before = *q;
    assert(submit_command(q, text) == result);
    assert(q->head == before.head && q->tail == before.tail);
    assert(q->count == before.count);
    for (unsigned i = 0; i < QUEUE_CAPACITY; ++i) {
        assert(q->slots[i] == before.slots[i]);
    }
}

int main(void)
{
    struct IntQueue q = {0};
    int value = -1;
    assert(submit_command(&q, "RUN") == SUBMIT_OK);
    expect_rejection(&q, NULL, SUBMIT_INVALID);
    expect_rejection(&q, "", SUBMIT_INVALID);
    expect_rejection(&q, "RUNx", SUBMIT_INVALID);
    assert(submit_command(&q, "STOP") == SUBMIT_OK);
    assert(submit_command(&q, "STOP") == SUBMIT_OK);
    expect_rejection(&q, "RUN", SUBMIT_FULL);
    expect_rejection(&q, "RUNx", SUBMIT_INVALID);
    assert(queue_pop(&q, &value) == QUEUE_OK && value == START);
    assert(submit_command(&q, "RUN") == SUBMIT_OK);
    assert(queue_pop(&q, &value) == QUEUE_OK && value == STOP);
    assert(queue_pop(&q, &value) == QUEUE_OK && value == STOP);
    assert(queue_pop(&q, &value) == QUEUE_OK && value == START);
    assert(queue_pop(&q, &value) == QUEUE_EMPTY);
    puts("D22_SUBMIT_CHECKS=PASS");
    return 0;
}
