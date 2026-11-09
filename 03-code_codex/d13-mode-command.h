#ifndef D13_MODE_COMMAND_H
#define D13_MODE_COMMAND_H

#define MODE_AUTO 1
#define MODE_MANUAL 2
#define MODE_UNKNOWN 0
#define MODE_NO_SEPARATOR (-1)
#define MODE_EMPTY (-2)
#define MODE_BAD_TAG (-3)
#define MODE_BAD_BUFFER (-4)

int classify_mode(char *text, int capacity);
void trim_right_spaces(char *text);

#endif
