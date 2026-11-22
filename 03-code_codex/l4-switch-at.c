#include "l4-switch-at.h"

unsigned int set_switch_at(unsigned int flags, int bit, int enabled)
{
    unsigned  int mask = 1u << bit;
    unsigned  int a = set_switch(flags, mask, enabled);
    return a;
}