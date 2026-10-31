#include <assert.h>
int text_length(const char *text){int n=0;while(text[n]!='\0'){n++;}return n;}
int copy_text(char destination[],int capacity,const char source[]){int length=text_length(source);if(capacity<=length){return 0;}for(int i=0;i<=length;i++){destination[i]=source[i];}return 1;}
int main(void){char a[6]="OLD";assert(copy_text(a,6,"HELLO")==1);assert(a[0]=='H'&&a[4]=='O'&&a[5]=='\0');char b[6]="OLD";assert(copy_text(b,6,"HELLOO")==0);assert(b[0]=='O'&&b[1]=='L'&&b[2]=='D'&&b[3]=='\0');char c[1]={'Z'};assert(copy_text(c,0,"")==0&&c[0]=='Z');assert(copy_text(c,1,"")==1&&c[0]=='\0');return 0;}
