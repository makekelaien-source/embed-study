#include <stdio.h>
int find_char_index(const char *text, int capacity, char target);

int main (void){
    char group[8] = "AB;CD";
    int capacity = sizeof(group ) / sizeof (group[0]);
    char target = ';' ;
    scanf ("%c",&target);
    printf ("%d",find_char_index(group,capacity,target));
    return 0 ;
    
}

int find_char_index(const char *text, int capacity, char target){
    for (int i = 0; i < capacity ; i++)
    {
        if (text [i] == target)
        {
            return i;
        }else if(text[i] == '\0'){
        return -1;
    }
    }
    return -1 ;    
}