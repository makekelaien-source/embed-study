#include <stdio.h>
 int main(void){
    char text[16] ;
    char *p = fgets(text,sizeof text,stdin);

 if (p != NULL)
 {
    if (ferror(stdin) == 0)
    {
        return 0;
    }
    fputs ("OK\n",stdout);
    return 0; /*读取成功*/
 }else {
    if (ferror(stdin) == 0)
    {
        fputs("NO_INPUT\n",stderr);
        return 0 ;
    }
    else{
    fputs("READ_ERROR\n",stderr);
    return 1;}
 }
}
 