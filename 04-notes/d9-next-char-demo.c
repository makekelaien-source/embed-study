/* Teacher example: reuse student read_text and inspect the next input character. */
#define main d9_student_original_main
#include "../03-code_codex/d9-line-reader.c"
#undef main
int main(void)
{
    char text[8];
    int status = read_text(text, sizeof text);
    printf("STATUS=%d\n", status);
    if (status == 2) {
        int ch = fgetc(stdin);
        if (ch == EOF) puts("NEXT=EOF");
        else printf("NEXT=%d\n", ch);
    }
    return 0;
}
