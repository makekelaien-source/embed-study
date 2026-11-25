#include "D20-list-node.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
    struct Node last = {37, NULL};
    struct Node middle = {12, &last};
    struct Node front = {12, &middle};
    struct Node *head = list_detach_front(&front);
    assert(head == &middle && front.next == NULL);
    assert(middle.next == &last && last.next == NULL);
    assert(list_detach_front(head) == &last && middle.next == NULL);
    assert(list_detach_front(&last) == NULL && last.next == NULL);
    assert(list_detach_front(NULL) == NULL);
    assert(front.value == 12 && middle.value == 12 && last.value == 37);
    puts("LIST_DETACH_CHECKS=PASS");
    return 0;
}
