#ifndef D20_LIST_NODE_H
#define D20_LIST_NODE_H

#include <stddef.h>

struct Node {
    int value;
    struct Node *next;
};

struct Node *list_prepend(struct Node *head, struct Node *node);

struct Node *list_detach_front(struct Node *head);

#endif
