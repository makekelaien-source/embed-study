#include <stdio.h>
struct Reading { int value; };
void by_value(struct Reading r) { r.value = 99; printf("inside=%d\n", r.value); }
void by_pointer(struct Reading *p) { p->value = 99; }
int main(void) {
    struct Reading a = {25};
    by_value(a);
    printf("after_value=%d\n", a.value);
    by_pointer(&a);
    printf("after_pointer=%d\n", a.value);
    return 0;
}
