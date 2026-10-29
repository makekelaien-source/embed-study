#include <stdio.h>
#define sam 10

int pin (int a){
    
    if ( a < 0 && a != -999)
    {
        return -1 ;
    }else if (a >= 30)
    {
        return 1 ;
    }else if (a == -999){
        return 2 ;
        }
    else return 0 ;
    }
    
    

int main(void){
    int temp[sam] = {-999,-2,20,30,31,32,18,-999,33,34};
    int useless = 0 ; int useful = 0 ; float sum = 0 ; float ave = 0 ;
    int cold = 0 ; int hot = 0 ; int normal = 0 ;
    int hot_con = 0; int hot_conmax = 0 ;int position = -1 ;
    for (int i = 0; i < sam ; i++)
    {
        if (temp [i] == -999)
        {
            useless ++ ; 
        }else {useful++;
        sum += temp [i];}
        
        if (pin (temp [i]) == 1)
        {
            hot ++;
            hot_con ++;
            if (hot_con > hot_conmax)
            {
                hot_conmax = hot_con;
            }
            
        }else if (pin (temp [i]) == -1)
        {
            cold ++ ;
            hot_con = 0 ;
        }else if (pin (temp [i]) == 0)
        {
            normal ++; 
            hot_con = 0 ;
        }else hot_con = 0 ;
        
        while (hot_conmax ==3 && position == -1)
        {
            position = i;
            break;
        }
        
        
        
        
        
    }

    
    printf("无效个数：%d\n有效个数:%d\n低温个数:%d\n正常个数:%d\n高温个数:%d\n有效温度综合:%.0f\n",useless,useful,cold,normal,hot,sum);
    if (useful == 0)
    {printf ("无有效数据\n");
    }else {ave = sum / useful ;
    printf ("有效温度均值%.2f\n",ave);}
    printf ("最长连续高温数%d\n",hot_conmax);
    printf("首次触发警报下标为%d",position);
    
    
    return 0 ;
}