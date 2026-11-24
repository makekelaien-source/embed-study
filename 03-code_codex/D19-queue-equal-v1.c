#include "D19-ring-queue.h"

int queue_equal(const struct IntQueue *a, const struct IntQueue *b){
    int c = 1;
    int d = a->head ; int e = b->head ;
    int counta = a->count; int countb = b->count ;
    if (a->count == 0 && b->count == 0)
    {  
        return c;
    }
    while (a->count == b->count )
    {
        if (a->count == 0)
        {
            return c;
        }else if (a->slots[d] == b->slots[e])
        {
            d = (d + 1 ) % 3 ;
            e = (e + 1 ) % 3 ;
            counta -- ; countb -- ;
            continue;
        }else if (a->slots[d] != b->slots[e])
        {
            break;
        }
    }
    return 0;
    
    
}