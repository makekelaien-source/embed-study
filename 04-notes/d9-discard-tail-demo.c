/* Teacher demonstration reusing the student reader. */
#define main d9_student_original_main
#include "../03-code_codex/d9-line-reader.c"
#undef main

int main(void)
{
    char first[8];
    char second[8];
    int status = read_text(first, sizeof first);
    if (status == 2) {
        int ch = fgetc(stdin);
        while (ch != '\n' && ch != EOF) {
            ch = fgetc(stdin);
        }
    }
    int next_status = read_text(second, sizeof second);
    printf("NEXT_STATUS=%d\n", next_status);
    if (next_status == 1 || next_status == 2) {
        printf("NEXT_TEXT=[%s]\n", second);
    }
    return 0;
}
