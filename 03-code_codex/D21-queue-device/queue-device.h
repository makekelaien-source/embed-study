#ifndef D21_QUEUE_DEVICE_H
#define D21_QUEUE_DEVICE_H

#include "D19-ring-queue.h"
#include "D20-device-state.h"

enum QueueResult device_consume_one(struct IntQueue *q,
                                    enum DeviceState *state);

#endif
