#include <stdio.h>

int main(void)

{int i = 0;

    for ( i = 1; i <= 100; i++)
    {if (i % 7 == 0){
        printf ("%d是7的倍数\n",i);
    }
    }
return 0 ;
}
