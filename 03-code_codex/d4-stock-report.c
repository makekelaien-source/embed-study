#include <stdio.h>
#define count 4
#define start 5

int manipulate ( int a , int b ) ;

int main (void) {
    
    int storeage = start ;
    int least = start ;
    int group [count] = {3,-4,-8,2} ;
    int success = 0 ; int fail = 0 ; int position = -1 ;
    int least_positon = -1 ;
    
    for (int i = 0; i < count; i++)
    {
        
        if (manipulate (storeage , group [i]) == 0)
        {
            fail ++ ;
            if (position == -1)
            {
                position = i ;
            }    
        }else {
            storeage += group [i] ;
            success ++ ;
            if (least >= storeage)
            {
                least = storeage ;
                least_positon = i ;
            }
            

        }
           
    }

    printf ("最终库存%d,成功次数%d,拒绝次数%d,首次拒绝下标%d,历史最低库存%d",storeage, success , fail, position,least);
    return 0 ;
}

int manipulate (int a, int b){
    if (a + b < 0 || a + b > 10)
    {
        return 0 ;
    }
    else {
        return 1 ;
    }
}