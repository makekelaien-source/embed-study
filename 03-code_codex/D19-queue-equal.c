#include "D19-ring-queue.h"

int queue_equal(const struct IntQueue *a, const struct IntQueue *b){
    int c = 1;
    int d = a->head ; int e = b->head ;
    int counta = a->count; int countb = b->count ;
    if (counta != countb)
    {
        return 0;
    }
    
    if (a->count == 0 && b->count == 0)
    {  
        return c;
    }
    while (counta == countb )
    {
        if (counta == 0)
        {
            return c;
        }else if (a->slots[d] == b->slots[e])
        {
            d = (d + 1 ) % QUEUE_CAPACITY ;
            e = (e + 1 ) % QUEUE_CAPACITY ;
            counta -- ; countb -- ;
            continue;
        }else if (a->slots[d] != b->slots[e])
        {
            break;
        }
    }
    return 0;
    
    
}