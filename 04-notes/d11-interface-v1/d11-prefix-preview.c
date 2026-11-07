#include <stdio.h>
#include "d11-token-prefix.h"

int main(void){
    char text[] = "RUN AUTO";
    int a = token_prefix_length(text,sizeof text);
    printf ("%d",a);
    return 0;
}