#include <stdio.h>
int cut(char *text, int marker);

int main(void){
    char type [999];
    printf("输入一个文本，遇到；会停下来\n");
    if (scanf ("%998s",type) != 1)
    {
        return 1 ;
    }
    
    
    int marker = sizeof(type) / sizeof (type[0]);
    if (cut(type,marker)== 1)
    {
        printf("%s",type);
    }
    return 0 ;
}

int cut(char *text, int marker){
    for (int i = 0; i < marker && text[i] != '\0'; i++)
    {
        if (text [i] == ';')
        {
            text [i] = '\0' ;
            return 1;
        }
        
    }
    return 0 ;
    
}