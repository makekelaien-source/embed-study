#ifndef D10_READ_STATUS_H
#define D10_READ_STATUS_H

#include <stdio.h>

#define D10_READ_CHAR 1
#define D10_READ_END 0
#define D10_READ_ERROR (-1)
#define D10_READ_UNKNOWN (-2)

int classify_read(int ch, int end_flag, int error_flag);

#endif
