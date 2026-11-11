#include <stdio.h>
int main(void){
    enum HeatLevel{
        HEAT_LOW = 0,
        HEAT_NORMAL = 1 ,
        HEAT_HIGH = 2 ,
    };
    int temperatur ;
    scanf("%d",&temperatur);
        if (temperatur < 20)
        {
            enum HeatLevel level = HEAT_LOW;
            if (level == HEAT_LOW)
            {
                printf ("LOW");
            }
        }
        else if (temperatur >= 30 )
        {
            enum HeatLevel level = HEAT_HIGH;
            if (level == HEAT_HIGH)
            {
                printf ("HIGH");
            }
        }else {enum HeatLevel level = HEAT_NORMAL;   
            if (level == HEAT_NORMAL)
            {
                printf ("NORMAL");
            }}
    return 0 ;
}