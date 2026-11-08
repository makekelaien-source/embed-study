/* Teacher test substitute: inject a reader status, without touching student main. */
#include "d12-line-reader.h"
#ifndef TEST_READ_STATUS
#error TEST_READ_STATUS must be provided by the test command
#endif
int read_complete_line(char *dest,int capacity)
{
    (void)dest;
    (void)capacity;
    return TEST_READ_STATUS;
}
