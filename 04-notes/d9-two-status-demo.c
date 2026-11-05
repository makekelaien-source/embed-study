/* Teacher demo reuses student's current function without editing it. */
#define main d9_student_original_main
#include "../03-code_codex/d9-line-reader.c"
#undef main

int main(void)
{
    char first[8];
    char second[8];
    int a = read_text(first, sizeof first);
    int b = read_text(second, sizeof second);
    printf("FIRST_STATUS=%d\n", a);
    if (a == 1 || a == 2) printf("FIRST=[%s]\n", first);
    printf("SECOND_STATUS=%d\n", b);
    if (b == 1 || b == 2) printf("SECOND=[%s]\n", second);
    return 0;
}
