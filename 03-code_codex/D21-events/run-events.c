#include "run-events.h"
#include <assert.h>

enum DeviceState run_events(enum DeviceState initial,const enum DeviceEvent *events,size_t count){
    enum DeviceState first = initial;
    if (count == 0 || events ==NULL)
    {
        return initial;
    }
    else if (count > 0)
    {
        for (size_t i = 0; i < count; i++)
        {
            first = device_step(first,events[i]) ;
        }
        
    }
    return first;
    
}