#ifndef D20_DEVICE_STATE_H
#define D20_DEVICE_STATE_H
enum DeviceState { BOOT, IDLE, RUN, SAFE };
enum DeviceEvent { READY, START, STOP, FAULT, RESET };
enum DeviceState device_step(enum DeviceState current, enum DeviceEvent event);
#endif