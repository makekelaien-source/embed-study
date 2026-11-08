/* Intentionally faulty teacher variant; not the student's implementation. */
#include <string.h>
#include <stddef.h>
int command_kind_bad(const char *command)
{
    if (command == NULL) return -1;
    if (strcmp(command, "RUN")) return 1;
    if (strcmp(command, "STOP") == 0) return 2;
    return 0;
}
