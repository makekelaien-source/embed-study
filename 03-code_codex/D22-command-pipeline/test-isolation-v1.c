#include "submit-command.h"
#include <assert.h>
#include "queue-device-all.h"

int main(void){
    struct IntQueue q = {0};
    enum DeviceState state = IDLE;
    struct IntQueue qb = {0};
    enum DeviceState stateb = SAFE;
    assert (submit_command(&q,"RUN") == SUBMIT_OK);
    assert (q.count == 1);
    assert (state == IDLE);
    assert (qb.count == 0);
    assert (stateb == SAFE);
    assert (submit_command(&qb,"RUN") == SUBMIT_OK);
    assert (q.count == 1);
    assert (state == IDLE);
    assert (qb.count == 1);
    assert (stateb == SAFE);
    assert (device_consume_all(&q,&state) == QUEUE_OK);
    assert (q.count == 0);
    assert (state == RUN);
    assert (qb.count == 1);
    assert (stateb == SAFE);
    assert (device_consume_all(&qb,&stateb)== QUEUE_OK);
    assert (q.count == 0);
    assert (state == RUN);
    assert (qb.count == 1);
    assert (stateb == SAFE);
}