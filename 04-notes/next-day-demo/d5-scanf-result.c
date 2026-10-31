#include <stdio.h>
int main(void) {
    int number = 123;
    int matched = scanf("%d", &number);
    printf("matched=%d number=%d\n", matched, number);
    return 0;
}
