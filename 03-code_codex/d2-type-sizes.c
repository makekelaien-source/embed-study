#include <stdio.h>
int main(void){
    int number = 256;
    printf("%d\n%zu\n%zu\n%zu\n%zu",number,sizeof(number),sizeof (int),sizeof (float), sizeof (char));
}