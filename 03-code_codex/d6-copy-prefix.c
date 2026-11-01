#include <stdio.h>

int text_length(const char *text);
int copy_prefix(char *destination, int capacity, const char *source, int limit);

int main(void)
{
    char destination[4] = "OK";
    char source[] = "HELLO";
    int limit;

    if (scanf("%d", &limit) != 1 || limit < 0)
    {
        printf("INPUT_ERROR\n");
        return 1;
    }

    int capacity = sizeof(destination) / sizeof(destination[0]);
    int result = copy_prefix(destination, capacity, source, limit);
    printf("%d %s\n", result, destination);
    return 0;
}

/* Teacher-corrected core, at the student's explicit request. */
int copy_prefix(char *destination, int capacity, const char *source, int limit)
{
    if (capacity < 0 || limit < 0)
    {
        return 0;
    }

    int length = text_length(source);
    int count;
    if (length > limit)
    {
        count = limit;
    }
    else
    {
        count = length;
    }

    /* count text characters need one additional slot for the terminator. */
    if (capacity <= count)
    {
        return 0;
    }

    for (int i = 0; i < count; i++)
    {
        destination[i] = source[i];
    }
    destination[count] = '\0';
    return 1;
}

/* Teacher-supplied dependency: the student's existing text_length implementation. */
int text_length(const char *text){
    int i = 0 ;
    while (text [i] != '\0')
    {
        i ++ ;
        
    }return i ;
     
}
