#include "filter.h"

void smple_set_batch(struct SAMPLE samples[], int count, int bit, int enabled);

void smple_set_batch(struct SAMPLE samples[], int count, int bit, int enabled);{
    if (count == 0){
    }
    else {
        for (int i = 0; i < count; i++){   
            set_switch_at(samples[i],2,1);
            set_switch_at(samples[i],1,0);
    }
}
}