#include <assert.h>
int text_length(const char *text){int n=0;while(text[n]!='\0'){n++;}return n;}
int main(void){assert(text_length("CAT")==3);assert(text_length("")==0);char text[8]="OK";assert(text_length(text)==2);return 0;}
