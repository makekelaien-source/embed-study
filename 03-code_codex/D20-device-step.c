#include "D20-device-state.h"
#include <stdio.h>
enum DeviceState device_step(enum DeviceState current, enum DeviceEvent event){
    if (current == SAFE && event == RESET)
    {
        return BOOT;
    }else if (current == BOOT && event == READY)
    {
        return IDLE;
    }else if (current == IDLE && event ==START)
    {
        return RUN ;
    }else if (current == RUN && event == STOP)
    {
        return IDLE ;
    }else if (event == FAULT)
    {
        return SAFE;
    }else return current; 
}