#ifndef D21_RUN_EVENTS_H
#define D21_RUN_EVENTS_H

#include <stddef.h>
#include "D20-device-state.h"

enum DeviceState run_events(enum DeviceState initial,
                            const enum DeviceEvent *events,
                            size_t count);

#endif
