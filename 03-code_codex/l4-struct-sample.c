#include <stdio.h>
int main(void){
    struct Sample{
        int sensor_id;
        int temperatur;
    };
    struct Sample current ;
    scanf("%d",&current.sensor_id);
    scanf("%d",&current.temperatur);
    struct Sample snaphot = current;
    current.temperatur += 5;
    printf ("current: %d %d\n",current.sensor_id,current.temperatur);
    printf("snapshot: %d %d\n",snaphot.sensor_id,snaphot.temperatur);
    return 0;
}