/* Reused D7 student function; formatting normalized by teacher only. */
#ifndef D9_REFERENCE_HELPERS_H
#define D9_REFERENCE_HELPERS_H
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
#endif
