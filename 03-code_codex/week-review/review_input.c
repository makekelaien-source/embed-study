#include <stdio.h>
#include "review_input.h"

/* Teacher copy of your D9 read_text and check_tail. */
int read_text(char *dest, int capacity){
    if (capacity < 2)
    {
        return -1 ; /*容量小于2*/
    }
    if (fgets(dest,capacity,stdin) == NULL)
    {
        return 0 ; /*什么都没有返回0*/
    }
    for (int i = 0; i < capacity; i++)
    {
        if (dest[i] == '\n')
        {
            dest[i] = '\0';
            return 1 ; /*取到换行，令换行=0结束*/
        }
        else if (dest[i] == '\0')
    {
        return 2 ;  /*取到结束*/
    }
    
    }
    return 2 ;  
}

int check_tail(void){
    int a = fgetc(stdin);
    if (a == '\n')
    {
        return 1 ;  /*代表取到回车换行，再次进行read_text取新的*/
    }else if (a == EOF)
    {
        return 0 ; /*读取到错误*/
    }else {
        while (a != '\n' && a != EOF)
        {
            a = fgetc(stdin); /*读正常文本，一直读到出现前两种情况*/
        }
        
    }return 2 ;
}
