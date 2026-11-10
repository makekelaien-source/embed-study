#include <stdio.h>
#include <string.h>

int main(void)
{
    char text[16];

    while (fgets(text, sizeof text, stdin) != NULL) {
        if (strchr(text, '\n') != NULL) {
            fputs("OK\n", stdout);
            continue;
        }else{
            int ch = fgetc(stdin);
            if (ch == '\n' || ch == EOF)
            {
                fputs("OK\n", stdout);
                continue;
            }else fputs ("TOO_LONG\n",stderr);
            
            while (ch != '\n' && ch != EOF)
            {
                ch = fgetc(stdin);
            }
        }}
    return 0;
}