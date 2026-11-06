#ifndef D10_COMMAND_INPUT_H
#define D10_COMMAND_INPUT_H

#include "d10-command-policy.h"

#define COMMAND_INPUT_ERROR (-2)

/* Reads one line from stdin. capacity >= 2 allows a read.
 * text is usable only for COMPLETE and END_UNCONFIRMED.
 * eof_confirmed is set to 1 only for END_UNCONFIRMED with normal EOF.
 */
int d10_read_command(char *text, int capacity, int *eof_confirmed);

#endif
