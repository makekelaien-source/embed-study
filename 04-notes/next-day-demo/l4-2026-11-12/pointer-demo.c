#include <stdio.h>
struct Reading { int id; int value; };
void increase(struct Reading *p) { p->value += 1; }
int main(void) {
    struct Reading a = {7, 25};
    struct Reading b = a;
    struct Reading *p = &a;
    increase(p);
    printf("a=%d,%d b=%d,%d\n", a.id, a.value, b.id, b.value);
    return 0;
}
