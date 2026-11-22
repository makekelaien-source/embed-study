#include "sample.h"

void sample_refresh(struct Sample *sample){
    if (sample->temperature < 20)
    {
        sample->level = HEAT_LOW;
        sample->flags = set_switch_at(sample->flags,1,0);
    }else if (sample->temperature >= 30 )
    {
        sample->level = HEAT_HIGH;
        sample->flags = set_switch_at(sample->flags,1,1);
    }else{
        sample->level = HEAT_NORMAL;
        sample->flags = set_switch_at(sample->flags,1,0);
    }
}