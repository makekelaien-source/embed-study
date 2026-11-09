#include <stdio.h>
#include <string.h>

void trim_right_spaces(char *text);

int main(void)
{
    const char *inputs[] = {"RUN  ", "  RUN ", "RUN AUTO ", " ", "   ", "", "RUN", "RUN\t", "A B", "A B  C "};
    const char *expected[] = {"RUN", "  RUN", "RUN AUTO", "", "", "", "RUN", "RUN\t", "A B", "A B  C"};
    char buffer[101];
    int passed = 0;
    for (size_t i = 0; i < sizeof inputs / sizeof inputs[0]; ++i) {
        strcpy(buffer, inputs[i]);
        trim_right_spaces(buffer);
        if (strcmp(buffer, expected[i]) != 0) return 1;
        ++passed;
    }
    memset(buffer, 'X', 99);
    buffer[99] = ' ';
    buffer[100] = '\0';
    trim_right_spaces(buffer);
    if (strlen(buffer) != 99) return 1;
    printf("%d/11 passed\n", passed + 1);
    return 0;
}
