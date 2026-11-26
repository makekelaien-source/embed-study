#include "run-events.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
    enum DeviceState result;
    enum DeviceEvent normal[] = {READY, START, STOP};
    enum DeviceEvent partial[] = {FAULT, RESET, START};
    enum DeviceEvent recovery[] = {FAULT, RESET, READY, START};
    enum DeviceEvent limited[] = {READY, START, FAULT};
    enum DeviceEvent locked[] = {READY, START};

    result = run_events(BOOT, NULL, 0);
    assert(result == BOOT);
    result = run_events(IDLE, NULL, 0);
    assert(result == IDLE);
    result = run_events(RUN, NULL, 0);
    assert(result == RUN);
    result = run_events(SAFE, NULL, 0);
    assert(result == SAFE);

    result = run_events(BOOT, normal, 3);
    assert(result == IDLE);
    assert(normal[0] == READY && normal[1] == START && normal[2] == STOP);

    result = run_events(RUN, partial, 3);
    assert(result == BOOT);
    assert(partial[0] == FAULT && partial[1] == RESET && partial[2] == START);

    result = run_events(RUN, recovery, 4);
    assert(result == RUN);
    assert(recovery[0] == FAULT && recovery[1] == RESET);
    assert(recovery[2] == READY && recovery[3] == START);

    result = run_events(BOOT, limited, 2);
    assert(result == RUN);
    assert(limited[0] == READY && limited[1] == START && limited[2] == FAULT);

    result = run_events(SAFE, locked, 2);
    assert(result == SAFE);
    assert(locked[0] == READY && locked[1] == START);

    puts("EVENT_SEQUENCE_CHECKS=PASS");
    return 0;
}
