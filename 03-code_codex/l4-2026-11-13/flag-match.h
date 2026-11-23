#ifndef D18_FLAG_MATCH_H
#define D18_FLAG_MATCH_H

#include "filter.h"

/* Teacher helper: mask is 1..7, mode is MATCH_ANY or MATCH_ALL. */
static inline int flags_match(unsigned int flags, unsigned int mask,
                              enum FlagMatch mode)
{
    unsigned int selected = flags & mask;
    if (mode == MATCH_ALL) {
        return selected == mask;
    }
    return selected != 0u;
}

#endif
