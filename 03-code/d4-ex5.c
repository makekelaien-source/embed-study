#include <stdio.h>
int main(void)
{
    int i = 0;
    int weight = 0; int number = 0; int Fat= 0; int thin = 0 ;
    for ( number = 1 ; number <= 10; number++)
    {
        printf ("第%d个学生体重是多少斤\n",number);
        scanf("%d",&weight);
        if (weight >=160){
            Fat++;
        }else if (weight <=80){
            thin++;
        }
        
        
    }
    if (Fat > thin)
    {i++;
        
    }
    switch (i)
    {
    case 1:
        printf ("学生群体偏胖");/* code */
        break;
    
    default:
        printf ("学生群体偏瘦");
        break;
        
    }
    return 0 ;
    
}