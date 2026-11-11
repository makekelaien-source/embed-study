#ifndef L4_SWITCH_AT_H
#define L4_SWITCH_AT_H
unsigned int set_switch(unsigned int flags, unsigned int mask, int enabled);
unsigned int set_switch_at(unsigned int flags, int bit, int enabled);
#endif
