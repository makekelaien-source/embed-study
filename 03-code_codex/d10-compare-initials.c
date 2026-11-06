#include <stdio.h>
int back(char *text, int capacity);

int main(void){
    char text [7] ;
    if (fgets(text,sizeof text, stdin) == NULL)
    {
        printf ("MISSING");
        return 0;
    }
    int ch = fgetc(stdin);
    if (ch == EOF)
    {
        printf ("MISSING");
        return 0;
    }
    
    if (back(text,sizeof text) == 1){
        if (ch == text[0])
        {
            puts ("SAME");
        }   else puts ("DIFFERENT");}
    else {
        while (ch != '\n' && ch != EOF && ch != '\0'){
            ch = fgetc(stdin);}
            if (ch == '\n') {
    ch = fgetc(stdin);  // 第一行结束了，尝试读第二行首字母
}
if (ch == EOF) {
    puts("MISSING");
    return 0;
}
            if (ch == text[0]){
            puts ("SAME");
        }   else puts ("DIFFERENT");
    }
    
    return 0;   
}

int back(char *text, int capacity){
    for (int i = 0; i < capacity && text[i] != '\0'; i++) {
        if (text[i] == '\n') {
            return 1;  // 已找到换行
        }
    }
    return 0; 
}


/*先取走第一个，分两种情况，取到\n和取满
1.如果到\n 后面可以进入正常对比；
2.如果取到'\0'后面分两种情况
A后面还有正文，需要继续跑完剩余正文，然后遇到\n跑第二行
B第二行什么都没有*/