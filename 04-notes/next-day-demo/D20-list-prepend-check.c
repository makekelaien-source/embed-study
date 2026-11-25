#include "D20-list-node.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
    struct Node first = {37, NULL};
    struct Node same = {37, NULL};
    struct Node front = {8, NULL};
    struct Node *head = list_prepend(NULL, &first);
    assert(head == &first && first.value == 37 && first.next == NULL);
    head = list_prepend(head, &same);
    assert(head == &same && same.next == &first && same.value == 37);
    head = list_prepend(head, &front);
    assert(head == &front && front.value == 8 && front.next == &same);
    assert(same.value == 37 && same.next == &first);
    assert(first.value == 37 && first.next == NULL);
    puts("LIST_PREPEND_CHECKS=PASS");
    return 0;
}
