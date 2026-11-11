/* Teacher harness. Student implements record_event in the separate source. */
#include <stdio.h>
int record_event(int reset);
int main(void)
{
    int actions[] = {0, 0, 1, 0, 1, 1, 0};
    for (int i = 0; i < 7; i++) {
        int result = record_event(actions[i]);
        printf("%d\n", result);
    }
    return 0;
}
