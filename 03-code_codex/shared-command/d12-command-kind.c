#include <string.h>

int command_kind(const char *command){
    if (command == NULL)
    {
        return -1;
    }
    else if (strcmp(command,"STOP") == 0){
        return 2;
    }
    else if (strcmp(command,"RUN") == 0)
    {
        return 1;
    }else return 0;
}