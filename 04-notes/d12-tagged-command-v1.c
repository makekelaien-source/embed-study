#include <stdio.h>
#include "shared-text/d11-after-delimiter.h" /*capacity = 0 delimiter = '\0' text[a]= 0 返回NULL*/
#include "d12-command-kind.h"                /*其他时候返回分隔符后面的字符地址*/
                                             /*NULL 返回-1 RUN 1 STOP2 其他0*/
int tagged_command_kind(const char *text, int capacity){
    int a = after_delimiter(text,capacity,'/');
    return command_kind(a);       
}


/* 已有接口：
const char *after_delimiter(const char *text, int capacity, char delimiter);
int command_kind(const char *command);
*/