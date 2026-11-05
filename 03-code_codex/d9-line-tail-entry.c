/* Teacher harness. The student writes only check_tail. */
#define main d9_student_original_main
#include "d9-line-reader.c"
#undef main
#include "d9-line-tail.c"

int main(void)
{
    char first[8];
    char second[8];
    int status = read_text(first, sizeof first);
    if (status == 2) {
        printf("TAIL=%d\n", check_tail());
    }
    int next = read_text(second, sizeof second);
    printf("NEXT=%d\n", next);
    if (next == 1 || next == 2) {
        printf("TEXT=[%s]\n", second);
    }
    return 0;
}
