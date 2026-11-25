#include "D20-list-node.h"
struct Node *list_prepend(struct Node *head, struct Node *node){
    head->value = node->value;
    return node->next;
}