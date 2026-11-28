#include "sample-stats.h"
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
int main(void)
{
    int a[] = {23, -999, 25, -999, 24};
    struct SampleStats s = summarize_samples(a, 5);
    assert(s.valid_count == 3 && s.invalid_count == 2 && s.sum == 72 && s.average == 24.0f);
    int b[] = {20, -999, 30};
    s = summarize_samples(b, 3);
    assert(s.valid_count == 2 && s.invalid_count == 1 && s.sum == 50 && s.average == 25.0f);
    int c[] = {-999, -999};
    s = summarize_samples(c, 2);
    assert(s.valid_count == 0 && s.invalid_count == 2 && s.sum == 0 && s.average == 0.0f);
    s = summarize_samples(NULL, 0);
    assert(s.valid_count == 0 && s.invalid_count == 0 && s.sum == 0 && s.average == 0.0f);
    int e[] = {-3};
    s = summarize_samples(e, 1);
    assert(s.valid_count == 1 && s.invalid_count == 0 && s.sum == -3 && s.average == -3.0f);
    int f[] = {-2, 1};
    s = summarize_samples(f, 2);
    assert(s.valid_count == 2 && s.invalid_count == 0 && s.sum == -1 && s.average == -0.5f);
    int g[] = {0};
    s = summarize_samples(g, 1);
    assert(s.valid_count == 1 && s.invalid_count == 0 && s.sum == 0 && s.average == 0.0f);
    assert(a[0] == 23 && a[1] == -999 && a[2] == 25 && a[3] == -999 && a[4] == 24);
    puts("D22_STATS_CHECKS=PASS");
    return 0;
}
