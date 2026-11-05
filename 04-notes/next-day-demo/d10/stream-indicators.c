#include <stdio.h>

int main(int argc, char **argv)
{
    FILE *input = stdin;
    if (argc == 2) {
        /* Teacher-only fixture: exclusive creation prevents overwriting a file. */
        input = fopen(argv[1], "wx");
        if (input == NULL) {
            puts("FIXTURE_OPEN_FAILED");
            return 2;
        }
    }
    int ch = fgetc(input);
    if (ch == EOF) {
        printf("END=%d ERROR=%d\n", feof(input) != 0, ferror(input) != 0);
    } else {
        printf("CHAR=%c\n", ch);
    }
    if (input != stdin) {
        fclose(input);
    }
    return 0;
}
