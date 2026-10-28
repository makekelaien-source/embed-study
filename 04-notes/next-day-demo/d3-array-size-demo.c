#include <stdio.h>

int main(void)
{
    int values[3] = {2, 4, 6};
    printf("%zu\n%zu\n", sizeof(values), sizeof(values[0]));
    return 0;
}
