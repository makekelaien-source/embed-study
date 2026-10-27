#include <stdio.h>

    int try_double (int n){
    n = n *2 ;
    return n ;
}
    
    int main(void){
        int v = 10;
        try_double(v);
        printf("v=%d\n",v);
        return 0 ;
    }

