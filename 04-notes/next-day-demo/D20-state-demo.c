#include <stdio.h>
#include "D20-device-state.h"
#ifndef CHECK_DEVICE
enum Lamp { OFF, ON };
enum Command { PRESS, WAIT };

static enum Lamp lamp_step(enum Lamp state, enum Command command)
{
    if (command == PRESS) {
        if (state == OFF) return ON;
        return OFF;
    }
    return state;
}

int main(void)
{
    enum Lamp state = OFF;
    const enum Command events[] = {PRESS, WAIT, PRESS};
    printf("OFF");
    for (unsigned int i = 0; i < 3; ++i) {
        state = lamp_step(state, events[i]);
        printf(" %s", state == ON ? "ON" : "OFF");
    }
    putchar('\n');
    return 0;
}
#else
int main(void)
{
    const enum DeviceState states[] = {BOOT, IDLE, RUN, SAFE};
    const enum DeviceEvent events[] = {READY, START, STOP, FAULT, RESET};
    const enum DeviceState expected[4][5] = {
        {IDLE, BOOT, BOOT, SAFE, BOOT},
        {IDLE, RUN,  IDLE, SAFE, IDLE},
        {RUN,  RUN,  IDLE, SAFE, RUN},
        {SAFE, SAFE, SAFE, SAFE, BOOT}
    };
    for (unsigned int i = 0; i < 4; ++i) {
        for (unsigned int j = 0; j < 5; ++j) {
            if (device_step(states[i], events[j]) != expected[i][j]) {
                fprintf(stderr, "cell %u,%u\n", i, j);
                return 1;
            }
        }
    }
    const enum DeviceEvent path[] = {START, READY, START, FAULT, START, RESET, START, READY, START, STOP};
    const enum DeviceState next[] = {BOOT, IDLE, RUN, SAFE, SAFE, BOOT, BOOT, IDLE, RUN, IDLE};
    enum DeviceState current = BOOT;
    for (unsigned int i = 0; i < sizeof path / sizeof path[0]; ++i) {
        current = device_step(current, path[i]);
        if (current != next[i]) {
            fprintf(stderr, "path step %u\n", i + 1);
            return 2;
        }
    }
    puts("DEVICE_CHECKS=PASS");
    return 0;
}
#endif