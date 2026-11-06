#include <stdio.h>
#include "d10-command-input.h"
#include "week-review/review_input.h"

/* Teacher adapter around the retained D9 helpers. */
int d10_read_command(char *text, int capacity, int *eof_confirmed)
{
    *eof_confirmed = 0;
    int status = read_text(text, capacity);

    if (status == READ_TEXT_BAD_CAPACITY) {
        return COMMAND_BAD_CAPACITY;
    }
    if (status == READ_TEXT_NO_DATA) {
        return ferror(stdin) ? COMMAND_INPUT_ERROR : COMMAND_NO_DATA;
    }
    if (status == READ_TEXT_COMPLETE) {
        return COMMAND_COMPLETE;
    }

    int tail = check_tail();
    if (tail == CHECK_TAIL_NEWLINE) {
        return COMMAND_COMPLETE;
    }
    if (tail == CHECK_TAIL_EXTRA_TEXT) {
        return ferror(stdin) ? COMMAND_INPUT_ERROR : COMMAND_TOO_LONG;
    }

    *eof_confirmed = !ferror(stdin) && feof(stdin);
    return COMMAND_END_UNCONFIRMED;
}
