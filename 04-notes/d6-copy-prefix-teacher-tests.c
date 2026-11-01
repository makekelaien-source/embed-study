/* Teacher verification only; includes the student exercise without its main. */
#define main exercise_main
#include "../03-code_codex/d6-copy-prefix.c"
#undef main
#include <string.h>

int main(void)
{
    const char *texts[] = {"HELLO", "CAT", "HELLO", "HELLO", "", "", "A", "A", "HELLO", "CAT"};
    int capacities[] = {4, 4, 3, 1, 1, 0, 1, 2, 6, 10};
    int limits[] = {3, 5, 3, 0, 5, 0, 1, 1, 20, -1};
    int counts[] = {3, 3, 3, 0, 0, 0, 1, 1, 5, 0};
    int wants[] = {1, 1, 0, 1, 1, 0, 0, 1, 1, 0};
    int failures = 0;
    for (int k = 0; k < 10; k++)
    {
        /* Padded backing keeps the old buggy implementation's reads in bounds. */
        char source[32] = {0};
        strcpy(source, texts[k]);
        char destination[32];
        memset(destination, 'Z', sizeof(destination));
        memcpy(destination, "OK", 3);
        char expected[32];
        memcpy(expected, destination, sizeof(expected));
        int count = counts[k];
        int expected_result = wants[k];
        if (expected_result)
        {
            memcpy(expected, source, count);
            expected[count] = '\0';
        }
        int result = copy_prefix(destination, capacities[k], source, limits[k]);
        int passed = result == expected_result && memcmp(destination, expected, sizeof(expected)) == 0 && strcmp(source, texts[k]) == 0;
        printf("case%d %s\n", k + 1, passed ? "PASS" : "FAIL");
        if (!passed) failures++;
    }
    return failures ? 1 : 0;
}
