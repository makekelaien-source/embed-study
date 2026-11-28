#include "collect-samples.h"
#include <assert.h>
#include <stddef.h>
#include <stdio.h>

int main(void)
{
    int values[] = {20, -999, 30};
    int invalid[] = {-999, -999};
    struct SampleStats report = {7, 8, 9, 10.0f};
    enum CollectResult result;
    enum DeviceState inactive[] = {BOOT, IDLE, SAFE};
    for (int i = 0; i < 3; i++) {
        result = collect_samples(inactive[i], values, 3, &report);
        assert(result == COLLECT_INACTIVE);
        assert(report.valid_count == 7 && report.invalid_count == 8);
        assert(report.sum == 9 && report.average == 10.0f);
    }
    result = collect_samples(RUN, values, 3, &report);
    assert(result == COLLECT_OK);
    assert(report.valid_count == 2 && report.invalid_count == 1);
    assert(report.sum == 50 && report.average == 25.0f);
    assert(values[0] == 20 && values[1] == -999 && values[2] == 30);
    result = collect_samples(SAFE, values, 3, &report);
    assert(result == COLLECT_INACTIVE);
    assert(report.valid_count == 2 && report.invalid_count == 1);
    assert(report.sum == 50 && report.average == 25.0f);
    result = collect_samples(RUN, invalid, 2, &report);
    assert(result == COLLECT_NO_DATA);
    assert(report.valid_count == 0 && report.invalid_count == 2);
    assert(report.sum == 0 && report.average == 0.0f);
    result = collect_samples(RUN, NULL, 0, &report);
    assert(result == COLLECT_NO_DATA);
    assert(report.valid_count == 0 && report.invalid_count == 0);
    assert(report.sum == 0 && report.average == 0.0f);
    puts("D22_COLLECT_CHECKS=PASS");
    return 0;
}
