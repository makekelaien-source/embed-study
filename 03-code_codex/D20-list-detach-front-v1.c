#include "D20-list-node.h"
struct Node *list_detach_front(struct Node *head){
    if (head->next == NULL || head == NULL)
    {
        return NULL;
    }else {
        struct Node *AV = head->next;
        return AV;
    }
    
}