#include <stdio.h>

/* Precondition: text points to a live string with at least one character. */
const char *move_one(const char *text)
{
    return text + 1;
}

int main(void)
{
    char word[] = "GO";
    const char *result = move_one(word);
    printf("%s\n", result);
    return 0;
}
