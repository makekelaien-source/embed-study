#include <stdio.h>
#define num 4

int classify (int value){
    if (value < -20)
    {
        return -1 ;
    }else if (value > 80)
    {
        return 1 ;
    }else return 0 ;
    
}

int main(void){
    int input ; int processed = 0 ;int valid = 0 ;
    int high = 0 ; int low = 0 ; int fail = 0 ;
    int sum = 0 ; float mean = 0 ;
    int valid_min = 80;

    for (int i = 0; i < num ; i++)
    {
        int b = scanf ("%d",&input) ;
        if (b == 1)
            {
            processed ++ ;
               
            if (classify(input) == 1)
            {
                high ++;
            }else if (classify(input) == 0)
            {
                valid ++;
                sum += input ; 
                if (input < valid_min)
                {
                    valid_min = input ;
                }
                
            }else  low ++;
        }else {
            fail ++;
            break ;
        }
    }

    
    
    if (valid > 0)
    {
        printf("%d/%d/%d/%d%d\n",processed,valid,low,high,valid_min);
        mean = (float) sum / valid ;
        printf ("sum=%d\nmean%.2f",sum,mean);
        if (fail == 0){
    }   else printf ("INPUT_ERROR index=%d\n",processed);
    }
    else {
        printf("%d\nNA",sum);
    }
    
     
    return 0 ;
    
}
