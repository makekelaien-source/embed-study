#include "limit.h"

int is_warm(int temperature)
{
    return temperature >= WARM_LIMIT;
}
