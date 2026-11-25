#include "D20-list-node.h"
#include <stdlib.h>

int main(void)
{
    struct Node original = {37, NULL};
    struct Node *head = &original;
    struct Node *added = malloc(sizeof *added);
    if (added == NULL) return 1;
    added->value = 37;
    added->next = NULL;

    head = list_prepend(head, added);
    struct Node *old = head;
    head = list_detach_front(head);
    free(old);
    return 0;
}
