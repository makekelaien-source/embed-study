#include <stdio.h>
#include <stddef.h>
struct Layout { char tag; int value; char tail; };
int main(void) {
    printf("size=%zu align=%zu offsets=%zu,%zu,%zu\n",
           sizeof(struct Layout), _Alignof(struct Layout),
           offsetof(struct Layout, tag), offsetof(struct Layout, value), offsetof(struct Layout, tail));
    return 0;
}
