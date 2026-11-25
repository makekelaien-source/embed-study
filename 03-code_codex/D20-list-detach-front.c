#include "D20-list-node.h"
struct Node *list_detach_front(struct Node *head){
    if (head == NULL || head->next == NULL )
    {
        return NULL;
    }else {
        struct Node *AV = head->next;
        head->next = NULL;
        return AV;
    }
    
}