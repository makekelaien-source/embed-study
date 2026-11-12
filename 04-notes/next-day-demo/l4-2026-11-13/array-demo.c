#include <stdio.h>
struct Reading { int id; int value; };
int read_second(const struct Reading readings[], int count) {
    if (count < 2) return 0;
    return readings[1].value;
}
int main(void) {
    struct Reading readings[] = {{1, 10}, {2, 20}};
    struct Reading *p = &readings[1];
    p->value = 27;
    printf("first=%d second=%d read=%d\n", readings[0].value, readings[1].value, read_second(readings, 2));
    return 0;
}
