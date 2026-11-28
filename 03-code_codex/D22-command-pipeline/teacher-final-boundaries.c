#include "submit-command.h"
#include "queue-device-all.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
    struct IntQueue q = {0};
    enum DeviceState state = IDLE;
    enum QueueResult qr = device_consume_all(&q, &state);
    assert(qr == QUEUE_EMPTY && q.count == 0 && state == IDLE);

    enum SubmitResult sr = submit_command(&q, "STOP");
    assert(sr == SUBMIT_OK && q.count == 1 && state == IDLE);
    qr = device_consume_all(&q, &state);
    assert(qr == QUEUE_OK && q.count == 0 && state == IDLE);

    qr = queue_push(&q, FAULT);
    assert(qr == QUEUE_OK);
    sr = submit_command(&q, "RUN");
    assert(sr == SUBMIT_OK && state == IDLE);
    qr = queue_push(&q, RESET);
    assert(qr == QUEUE_OK && q.count == 3);
    qr = device_consume_all(&q, &state);
    assert(qr == QUEUE_OK && q.count == 0 && state == BOOT);

    state = SAFE;
    qr = queue_push(&q, RESET);
    assert(qr == QUEUE_OK);
    qr = queue_push(&q, FAULT);
    assert(qr == QUEUE_OK);
    sr = submit_command(&q, "RUN");
    assert(sr == SUBMIT_OK && state == SAFE);
    qr = device_consume_all(&q, &state);
    assert(qr == QUEUE_OK && q.count == 0 && state == SAFE);
    puts("D22_FINAL_BOUNDARIES=PASS");
    return 0;
}
