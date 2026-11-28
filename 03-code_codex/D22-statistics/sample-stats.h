#ifndef D22_SAMPLE_STATS_H
#define D22_SAMPLE_STATS_H
struct SampleStats {
    int valid_count;
    int invalid_count;
    int sum;
    float average;
};
struct SampleStats summarize_samples(const int samples[], int count);
#endif
