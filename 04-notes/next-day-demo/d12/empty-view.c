#include <stdio.h>
#include "d11-after-delimiter.h"
int main(void)
{
    char with_separator[]="CMD/";
    char without_separator[]="CMD";
    const char *first=after_delimiter(with_separator,sizeof with_separator,'/');
    const char *second=after_delimiter(without_separator,sizeof without_separator,'/');
    printf("found_empty=%d missing=%d\n",first!=NULL && first[0]=='\0',second==NULL);
    return 0;
}
