#include <stdio.h>
int read_text(char *dest, int capacity);

int main(void){
    char data[8];
    int capacity = sizeof data / sizeof data [0];
    int status = read_text(data,capacity);
    if (status != -1 && status != 0)
    {
        printf ("%s",data);
    }
    
    return 0 ;

}

int read_text(char *dest, int capacity){
    if (capacity < 2)
    {
        return -1 ;
    }
    if (fgets(dest,capacity,stdin) == NULL)
    {
        return 0 ;
    }
    for (int i = 0; i < capacity; i++)
    {
        if (dest[i] == '\n')
        {
            dest[i] = '\0';
            return 1 ;
        }
        else if (dest[i] == '\0')
    {
        return 2 ;  
    }
    }
    return 2 ;  
}