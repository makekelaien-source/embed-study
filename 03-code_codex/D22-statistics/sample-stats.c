#include "sample-stats.h"

/* Teacher extraction from D2 reference-d2-statistics.c.
   Reuses the student's fault rule and accumulation; returns fields to caller. */
int is_fault(int value)
{
    if (value == -999)
    {
        return 1;
    }else return 0;
}

struct SampleStats summarize_samples(const int samples[], int count)
{
    struct SampleStats result = {0};
    for (int i = 0; i < count; i++)
    {
        if (is_fault(samples[i]) == 1)
        {
            result.invalid_count++;
        }else {
            result.sum += samples[i];
            result.valid_count++;
            result.average = (float) result.sum / result.valid_count;
        }
    }
    return result;
}
