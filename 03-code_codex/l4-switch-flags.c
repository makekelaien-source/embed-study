#include <stdio.h>
unsigned int set_switch(unsigned int flags, unsigned int mask, int enabled);

unsigned int set_switch(unsigned int flags, unsigned int mask, int enabled){
    if (enabled == 0)
    {
        flags &= ~mask;
    }else flags |= mask;
    return flags;
    
}
