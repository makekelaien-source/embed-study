#ifndef D10_COMMAND_POLICY_H
#define D10_COMMAND_POLICY_H

/* Status values match the week-review read_command contract. */
#define COMMAND_BAD_CAPACITY (-1)
#define COMMAND_NO_DATA 0
#define COMMAND_COMPLETE 1
#define COMMAND_TOO_LONG 2
#define COMMAND_END_UNCONFIRMED 3

int command_is_usable(int status, const char *text, int eof_confirmed);

#endif
