/* Teacher acceptance harness. Student functions are separate blank files. */
#include <stdio.h>
#include "sample.h"
int main(void) {
    struct Sample a = {7, 25, HEAT_NORMAL, 5};
    struct Sample snapshot = a;
    struct Sample b = {8, 19, HEAT_HIGH, 7};
    sample_set_value(&a, 30);
    if (a.sensor_id != 7 || a.temperature != 30 || a.level != HEAT_NORMAL || a.flags != 5) return 1;
    sample_refresh(&a);
    sample_refresh(&b);
    if (a.level != HEAT_HIGH || a.flags != 7) return 2;
    if (b.level != HEAT_LOW || b.flags != 5) return 3;
    if (snapshot.sensor_id != 7 || snapshot.temperature != 25 || snapshot.level != HEAT_NORMAL || snapshot.flags != 5) return 4;
    int temperatures[] = {19, 20, 29, 30};
    enum HeatLevel expected[] = {HEAT_LOW, HEAT_NORMAL, HEAT_NORMAL, HEAT_HIGH};
    for (int i = 0; i < 4; i++) {
        struct Sample s = {9, temperatures[i], HEAT_LOW, 133};
        sample_refresh(&s);
        unsigned int flags_expected = i == 3 ? 135u : 133u;
        if (s.sensor_id != 9 || s.temperature != temperatures[i] || s.level != expected[i] || s.flags != flags_expected) return 5 + i;
    }
    puts("SAMPLE_CHECKS=PASS");
    return 0;
}
