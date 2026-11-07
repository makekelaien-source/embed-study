#include <stdio.h>
int main(void){char text[]="RUN AUTO";const char *result=text+4;printf("%s\n",result);if(result[0]!='\0'){text[result-text]='X';}printf("%s\n",result);return 0;}
