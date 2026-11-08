#include <string.h>
#include "d12-tagged-command.h" /*a为NULL 返回-1 a==0 返回-2 RUN 1 STOP2*/

int strict_command_kind(const char *text, int capacity){
    if (text == NULL)
    {
        return -1;
    }else{
        int ch = tagged_command_kind(text,capacity);
        for (int i = 0; i < capacity ; i++)
        {
            if (ch != -1){
                return -1 ; /*-1 没有分隔符*/
            }else {
                if (strncmp(text,"CMD/",4) != 0)
                {
                    return -3 ; /*-3 缺标签*/
                }else if (strncmp(text,"CMD/",4) == 0 )
                {
                    return ch;
                }
            } 
    }}
}