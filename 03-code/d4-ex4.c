#include <stdio.h>

int main(void)
{
    int i = 0;
    int temp = 0;
    int hot = 0;
    int a = 0;

    for (i = 1; i <= 7; i = i + 1)
    {
        printf("Day %d temp: ", i);
        scanf("%d", &temp);
        if (temp >= 35){
            hot++;
        }
        if (temp %2 != 0)
        {a++;
            /* code */
        }
        
        
        
        /* 空1: 昨天的 if-else if 五档链条, 命中酷暑时 hot = hot + 1 */
    }

    switch (hot)
    {case 0:
        printf ("本周凉爽\n");
        break;
     case 1:
        printf ("有一天酷暑\n");
        break;
    default:
    printf ("高温预警\n");        /* 空2: case 0 / case 1 / default, 每个都别忘 break */
    }
    printf ("本周有%d天为奇数气温",a);

    return 0;
}