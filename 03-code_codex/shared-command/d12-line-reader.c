/* Teacher integration adapter; student does not rewrite input parsing. */
#include <stdio.h>
#include <stddef.h>
#include "week-review/review_input.h"
#include "d12-line-reader.h"
int read_complete_line(char *dest, int capacity)
{
    if (dest == NULL || capacity < 2) return LINE_BAD_BUFFER;
    int status=read_text(dest,capacity);
    if (ferror(stdin)) return LINE_IO_ERROR;
    if (status == READ_TEXT_NO_DATA) return LINE_END;
    if (status == READ_TEXT_BAD_CAPACITY) return LINE_BAD_BUFFER;
    if (status == READ_TEXT_COMPLETE) return LINE_READY;
    int tail=check_tail();
    if (ferror(stdin)) return LINE_IO_ERROR;
    if (tail == CHECK_TAIL_EXTRA_TEXT) return LINE_TOO_LONG;
    return LINE_READY;
}
