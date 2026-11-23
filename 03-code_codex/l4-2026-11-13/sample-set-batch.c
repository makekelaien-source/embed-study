#include "filter.h"

void sample_set_batch(struct Sample samples[], int count, int bit, int enabled){
    if (count == 0){
    }
    else {
        for (int i = 0; i < count; i++){   
            samples[i].flags = set_switch_at(samples[i].flags,bit,enabled);
    }
}
}