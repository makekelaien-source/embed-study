#ifndef L4_FILTER_H
#define L4_FILTER_H
#include "../l4-2026-11-12/sample.h"
enum FlagMatch { MATCH_ANY = 0, MATCH_ALL = 1 };
int count_flagged(const struct Sample samples[], int count,
                  unsigned int mask, enum FlagMatch match);
void sample_set_batch(struct Sample samples[], int count, int bit, int enabled);
#endif
