/* Teacher acceptance harness; requires the student's previous and new cores. */
#include <stdio.h>
#include <stddef.h>
#include "filter.h"
int main(void) {
    struct Sample samples[] = {
        {1, 10, HEAT_LOW, 1}, {2, 20, HEAT_NORMAL, 3},
        {3, 30, HEAT_HIGH, 4}, {4, 25, HEAT_NORMAL, 0}
    };
    if (count_flagged(samples, 4, 3, MATCH_ANY) != 2) return 1;
    if (count_flagged(samples, 4, 3, MATCH_ALL) != 1) return 2;
    if (count_flagged(samples, 4, 4, MATCH_ANY) != 1) return 3;
    if (count_flagged(samples, 4, 7, MATCH_ALL) != 0) return 4;
    if (count_flagged(NULL, 0, 3, MATCH_ANY) != 0) return 5;
    if (count_flagged(NULL, 0, 3, MATCH_ALL) != 0) return 6;
    if (samples[0].flags != 1 || samples[1].flags != 3 || samples[2].flags != 4 || samples[3].flags != 0) return 7;
    sample_set_batch(samples, 4, 2, 1);
    unsigned int set_expected[] = {5, 7, 4, 4};
    for (int i = 0; i < 4; i++) if (samples[i].flags != set_expected[i]) return 8;
    sample_set_batch(samples, 4, 1, 0);
    unsigned int clear_expected[] = {5, 5, 4, 4};
    for (int i = 0; i < 4; i++) if (samples[i].flags != clear_expected[i]) return 9;
    if (samples[0].sensor_id != 1 || samples[0].temperature != 10 || samples[0].level != HEAT_LOW) return 10;
    sample_set_batch(NULL, 0, 2, 1);
    puts("FILTER_CHECKS=PASS");
    return 0;
}
