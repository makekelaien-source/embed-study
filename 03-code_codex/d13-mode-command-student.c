#include <stdio.h>
#include "d13-mode-command.h"
#include <string.h>

int front(char *text);

int classify_mode(char *text, int capacity){
    if (text == NULL)
    {
    }else {
        int front_length = strchr(text,'/');
    int mode = strncmp(text,"MODE/",5) ;
    text = front_back (text);
    const char *p = text[front_length+1];
    if (text == NULL || capacity < 1 || strchr(text,'\0') == NULL){
        return -4 ;
    }else if (front_length == NULL)
    {
        return -1 ;
    }else if (mode != 0)
    {
        return -3 ;
    }else if ( mode == 0 && (p[0] == ' '))
    {
        return 2;
    }else if ( mode == 0 && (p[0] == '\0'))
    {
        return 2;
    }else if ( mode == 0 && (p == "AUTO")){
        return 1 ;
    }else if ( mode == 0 && (p == "MANNUAL")){
        return 2 ;
    }else if ( mode == 0 && (p[0] != '\0')){
        return 0 ;}

    }
    
    
}

char front_back(char *text){
    trim_right_spaces(text);
    char *a = strchr(text,' ');
    int b = 1 ;
    while (a == b)
    {
        text = text + 1 ; 
        a = strchr(text,' ');
        b ++ ;
    }
    return text ;
}