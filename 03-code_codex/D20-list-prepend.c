#include "D20-list-node.h"
struct Node *list_prepend(struct Node *head, struct Node *node){
    node->next = head;
    return node;
}