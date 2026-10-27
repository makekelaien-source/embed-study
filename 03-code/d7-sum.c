#include <stdio.h>
int check(int guess, int answer){
    if (guess > answer)
    {
        return 1;
    }else if (guess < answer)
    {
         return -1;
    }else return 0;    

}
int main(void)
{
    int cnt = 0 ; int g;
    printf ("猜大小！\n");
    while (1)
    {
        
        scanf("%d",&g);
        cnt++;
        int result = check (g,77);
        if (result == 0)
    {
        printf("猜中了，次数%d\n",cnt);
        break;
    }else if (result == 1)
    {
        printf("猜大了！\n");
    }else printf("猜小了！\n");
    
}
    return 0 ;   
}