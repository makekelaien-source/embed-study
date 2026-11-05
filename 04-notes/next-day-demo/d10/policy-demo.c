#include <stdio.h>
#include "line-policy.h"

int main(void)
{
    int statuses[] = {-1, 0, 1, 2, 3};
    int count = sizeof statuses / sizeof statuses[0];
    for (int i = 0; i < count; i++) {
        printf("%d -> %d\n", statuses[i], may_show_text(statuses[i]));
    }
    return 0;
}
