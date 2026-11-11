#include <stdio.h>
#include <string.h>

int main(void){
    char text[16];
    const char *p = fgets(text,sizeof text,stdin);
    int N = 0 ;
    if (p == NULL)
    {
        return 0 ;
    }
    while (p != NULL)
    {
        char *nl = strchr(text, '\n');
        if (nl != NULL) {
            *nl = '\0';        /* '\n'在哪个地址，就把哪个位置改成'\0' */
        }if (strcmp(text,"RUN") == 0)
        {
            N ++ ;
            fputs("RUN_OK\n",stdout);
            p = fgets(text,sizeof text,stdin);
        }else if (strcmp(text,"STOP") == 0){
            N ++ ;
            fputs("STOP_OK\n",stdout);
            p = fgets(text,sizeof text,stdin);
        }else {
            N ++ ;
            fprintf (stderr,"line %d:BAD_COMMAND\n",N);
            p = fgets(text,sizeof text,stdin);    
    }
    }
    return 0 ;    
}