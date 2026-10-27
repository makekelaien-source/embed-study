/* d1-ex2-intro.c —— 练习 2：个人信息输入 */
/* 要求：依次输入 名字、年龄(整数)、身高(小数)，然后打印一行： */
/*   我是 张三，今年 25 岁，身高 1.75 米 */
/* 提示：字符串盒子写法 char name[20]; 读它用 scanf("%s", name)（不用 &） */
/*       年龄用 %d，身高用 float 和 %.2f */
#include <stdio.h>

int main(void)
{
    char name[20];
    int age;
    float height;/* TODO 定义三个盒子：name（字符数组）、age（int）、height（float） */
    scanf ("%s", name);
    scanf ("%d", &age);
    scanf ("%f", &height);   /* TODO 依次 scanf 读入三个值（注意哪个不用加 &） */
    printf ("我是%s,今年%d,身高%.2f米",name,age,height); /* TODO 一行 printf 按上面的样子输出 */
    return 0;
}
