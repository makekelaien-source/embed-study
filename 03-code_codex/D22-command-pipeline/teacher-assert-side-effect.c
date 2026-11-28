#include <assert.h>
#include <stdio.h>
int main(void)
{
    int count = 0;
    assert(++count == 1);
    printf("%d\n", count);
    return 0;
}
