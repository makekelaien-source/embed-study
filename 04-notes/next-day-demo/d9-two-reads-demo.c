#include <stdio.h>
int main(void) {
    char first[8];
    char second[8];
    if (fgets(first, sizeof first, stdin) == NULL) return 0;
    if (fgets(second, sizeof second, stdin) == NULL) return 0;
    printf("FIRST=[%s]\nSECOND=[%s]\n", first, second);
    return 0;
}
