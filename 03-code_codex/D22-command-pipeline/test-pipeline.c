#include "submit-command.h"
#include <assert.h>
#include "queue-device-all.h"

int main(void){
    struct IntQueue q = {0};
    enum DeviceState state = IDLE;
    struct IntQueue qb = {0};
    enum DeviceState stateb = SAFE;
    enum SubmitResult result1 = submit_command(&q,"RUN");
    assert (result1 == SUBMIT_OK);
    assert (q.count == 1);
    assert (state == IDLE);
    assert (qb.count == 0);
    assert (stateb == SAFE);
    enum SubmitResult result2 = submit_command(&qb,"RUN");
    assert (result2 == SUBMIT_OK);
    assert (q.count == 1);
    assert (state == IDLE);
    assert (qb.count == 1);
    assert (stateb == SAFE);
    enum QueueResult result3 = device_consume_all(&q,&state);
    assert (result3 == QUEUE_OK);
    assert (q.count == 0);
    assert (state == RUN);
    assert (qb.count == 1);
    assert (stateb == SAFE);
    enum QueueResult result4 = device_consume_all(&qb,&stateb);
    assert (result4== QUEUE_OK);
    assert (q.count == 0);
    assert (state == RUN);
    assert (qb.count == 0);
    assert (stateb == SAFE);
}