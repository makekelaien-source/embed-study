# L4：static局部变量与存储期

2026-11-11同日接续，学生明确停止enum当前练习，按原计划下一单元继续。static此前未授；作用域仅复习必要区别。

目标：区分名称可见范围与对象存活时间，解释普通自动局部变量与static局部变量跨调用的差异。本次预案40分钟：讲解15、预测5、核心练习15、验证5；实际另计，备课不计学习。

普通函数内int count=0每次调用执行到声明时初始化新对象为0；离开该次调用作用范围后对象寿命结束。static int count=0具有静态存储期，程序启动前初始化一次，整个程序执行期间存在；后续调用不因再次经过声明而重置。没有显式初始化时static整数默认为0；普通未初始化局部整数不能按0使用。局部static名称仍只有块作用域，不会自动成为全局名称。可正常修改，不等同const；程序重新启动后重新初始化，不是磁盘/掉电持久化；共享状态存在测试和并发限制，后续展开。C中的静态存储期初始化式须满足常量初始化规则，不演示参数初始化。

教师对照例：

```c
#include <stdio.h>
void ordinary(void)
{
    int count = 0;
    count++;
    printf("%d\n", count);
}
void persistent(void)
{
    static int count = 0;
    count++;
    printf("%d\n", count);
}
int main(void)
{
    ordinary(); ordinary(); ordinary();
    persistent(); persistent(); persistent();
    return 0;
}
```

教师严格C11含-Werror编译0诊断，运行退出0，输出1/1/1/1/2/3。逐次：普通每次0→1→返回对象寿命结束；static同一个对象0→1→2→3，函数返回期间继续存在。

预测：把persistent中count++改为count+=2，重新启动程序后连调三次，输出什么？学生待答。
