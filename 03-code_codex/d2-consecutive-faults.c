#include <stdio.h>
#define sample 8

int main(void)
{
    int con = 0 ; int con_max = 0 ;
    int sam [sample] = {-999, -999, 23, -999, -999, -999, 24, -999};

    for (int i = 0; i < sample ; i++)
    {
        if ( sam [i] == -999)
        {
            con++;
            if (con > con_max)
            {
                con_max = con;
            }
            
        }else con = 0;
        
        
    }
    printf ("最长连续故障次数：%d\n",con_max);
    if (con_max >= 3)
    {
        printf ("报警");
    }else printf ("正常");

    return 0 ;

}