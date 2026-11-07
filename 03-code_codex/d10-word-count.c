#include <stdio.h>
int main(void){
    int ch = fgetc(stdin);
    int length = 0;
    while (ch != EOF){
        if (ch == '\n' || ch == ' ')
        {
            ch = fgetc(stdin);
        }else 
        {
            length ++ ;
            while (ch != '\n' && ch != ' '&& ch != EOF)
            {
                ch = fgetc(stdin);
            }
            continue;
        }
    } 
    printf ("%d",length);
    return 0 ;
}