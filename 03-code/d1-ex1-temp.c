/* d1-ex1-temp.c —— 练习 1：摄氏转华氏 */
/* 公式：华氏 = 摄氏 * 9 / 5 + 32 */
/* 要求：scanf 读入一个摄氏温度（小数），打印华氏值，保留 1 位小数 */
/* 提示：用 float；printf 用 %.1f；小心整数除法的坑 */
#include <stdio.h>

int main(void)
{
    float celsius = 0.0f; /* TODO 第 1 步：定义一个 float 变量 celsius，先给个初值 0.0f */
    printf ("请输入摄氏温度："); scanf ("%f", &celsius); /* TODO 第 2 步：printf 提示用户输入，然后 scanf 读进 celsius（别忘 &） */
    float fahrenheit = celsius * 9.0f / 5.0f + 32.0f; /* TODO 第 3 步：定义 float fahrenheit = 用公式算出来 */
    printf ("华氏温度=%.1f\n", fahrenheit); /* TODO 第 4 步：printf 输出结果，格式 %.1f，结尾带 \n */
    return 0;
}
