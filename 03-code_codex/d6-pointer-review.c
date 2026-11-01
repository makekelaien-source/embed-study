#include <stdio.h>
void read_at(char text[],int index, char *output){
    *output = text [index] ;


}

int main(void){
    char word [6] = "CODE";
    char selected = '?';
    int index = 2 ;
    read_at (word,index,&selected);
    word [index] = '\0';
    printf ("%c、%s",selected, word);
    return 0;
}