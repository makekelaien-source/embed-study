#include "submit-command.h"
#include <assert.h>
#include "queue-device-all.h"

int main(void){
    struct IntQueue q = {0};
    enum DeviceState state = IDLE;
    assert (submit_command(&q,"RUN") == SUBMIT_OK);
    assert (q.count == 1);
    assert (state == IDLE);
    assert (device_consume_all(&q,&state) == QUEUE_OK);
    assert (q.count == 0);
    assert (state == RUN);
    assert (submit_command(&q,"STOP")== SUBMIT_OK);
    assert (q.count == 1);
    assert (state == RUN);
    assert (device_consume_all(&q,&state)== QUEUE_OK);
    assert (q.count == 0);
    assert (state == IDLE);
    
}