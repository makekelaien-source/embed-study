#include "filter.h"

int count_flagged(const struct Sample samples[], int count, unsigned int mask, enum FlagMatch match);

int count_flagged(const struct Sample samples[], int count, unsigned int mask, enum FlagMatch match){
    int a = 0 ;
    if (count == 0)
    {
    }
    else{ 
        for(int i = 0; i < count; i++){
            if (match == MATCH_ANY && samples[i].flags & mask != 0)
            {
                a++;
            }
            else if (match = MATCH_ALL && samples[i].flags & mask == 3)
            {
                a++;
            }     
        }
    }
    return a;
}
