#ifndef L4_SAMPLE_H
#define L4_SAMPLE_H
#include "../l4-switch-at.h"
enum HeatLevel { HEAT_LOW = 0, HEAT_NORMAL = 1, HEAT_HIGH = 2 };
struct Sample {
    int sensor_id;
    int temperature;
    enum HeatLevel level;
    unsigned int flags;
};
void sample_set_value(struct Sample *sample, int temperature);
void sample_refresh(struct Sample *sample);
#endif
