#include <stdio.h>

void print_number(int number)
{
    printf("number=%d\n", number);
}

void write_number(int *address)
{
    *address = 37;
}

int main(void)
{
    int value = 10;
    int target = 20;
    int *ptr = &target;

    print_number(value);
    print_number(*ptr);

    write_number(&value);
    printf("after_address value=%d target=%d\n", value, target);

    write_number(ptr);
    printf("after_pointer value=%d target=%d\n", value, target);
    return 0;
}
