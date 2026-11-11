#include "classify.h"
#include <string.h>

int classify_command(const char *cmd)
{
    if (strcmp(cmd, "RUN") == 0) return 1;
    if (strcmp(cmd, "STOP") == 0) return 2;
    return 0;
}