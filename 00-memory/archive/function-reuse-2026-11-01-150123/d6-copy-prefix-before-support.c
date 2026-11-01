#include <stdio.h>
int copy_prefix(char *destination, int capacity, const char *source, int limit);

int main (void){
    char destination[4] = "OK";
    char source[] = "HELLO";
    int limit ;
    scanf ("%d",&limit);
    int capacity = sizeof (destination) / sizeof (destination[0]);
    if (copy_prefix(destination,capacity,source,limit) == 1)
    {
        printf ("1 %s",destination);    
    }
    return 0 ;
    
    
    
}

int copy_prefix(char *destination, int capacity, const char *source, int limit){
    int capacity2 = sizeof(source) / sizeof (*source);
    int count ;
    if (capacity2 > limit)
    {
        count = limit;
    }else {count = capacity2 ;
    }
    if (capacity >= count )
    {
        for (int i = 0; i < count ; i++)
        {
            destination[i] = source[i];
            destination[i+1] = '\0';
        }
        
        return 1 ; 
    }return 0 ;  
}

