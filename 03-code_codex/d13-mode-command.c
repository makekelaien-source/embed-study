#include <string.h>
#include "d13-mode-command.h"

int classify_mode(char *text, int capacity)
{
    if (text == NULL || capacity < 1) {
        return MODE_BAD_BUFFER;
    }

    int length = 0;
    while (length < capacity && text[length] != '\0') {
        ++length;
    }
    if (length == capacity) {
        return MODE_BAD_BUFFER;
    }

    char *slash = strchr(text, '/');
    if (slash == NULL) {
        return MODE_NO_SEPARATOR;
    }
    if (strncmp(text, "MODE/", 5) != 0) {
        return MODE_BAD_TAG;
    }

    char *field = slash + 1;
    while (*field == ' ') {
        ++field;
    }
    trim_right_spaces(field);

    if (*field == '\0') {
        return MODE_EMPTY;
    }
    if (strcmp(field, "AUTO") == 0) {
        return MODE_AUTO;
    }
    if (strcmp(field, "MANUAL") == 0) {
        return MODE_MANUAL;
    }
    return MODE_UNKNOWN;
}
