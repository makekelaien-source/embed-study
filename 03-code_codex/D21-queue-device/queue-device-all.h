#ifndef D21_QUEUE_DEVICE_ALL_H
#define D21_QUEUE_DEVICE_ALL_H

#include "D19-ring-queue.h"
#include "D20-device-state.h"

enum QueueResult device_consume_all(struct IntQueue *q,
                                    enum DeviceState *state);

#endif
