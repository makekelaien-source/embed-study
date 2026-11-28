#ifndef D22_COLLECT_SAMPLES_H
#define D22_COLLECT_SAMPLES_H
#include "sample-stats.h"
#include "../D21-queue-device/D20-device-state.h"
enum CollectResult { COLLECT_OK, COLLECT_NO_DATA, COLLECT_INACTIVE };
enum CollectResult collect_samples(enum DeviceState state,
                                   const int samples[], int count,
                                   struct SampleStats *out);
#endif
