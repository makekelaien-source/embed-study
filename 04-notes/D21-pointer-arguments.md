# D21｜函数参数中的值、地址与解引用

本单元是队列集成题的局部前置补强。普通变量以 int 为例，指针变量以 int * 为例。先按函数形参类型判断需要整数还是整数地址，再确定调用表达式。

假设调用方已有 int value = 10; int target = 20; int *ptr = &target;。

| 函数形参 | 调用方使用 value | 调用方使用 ptr |
|---|---|---|
| int number，接收整数值 | value | *ptr |
| int *address，接收整数地址 | &value | ptr |

&value 取得整数对象地址。ptr 已保存一个整数对象地址。*ptr 访问该地址所指的整数对象，放在右侧可以读取，放在赋值左侧可以修改。&ptr 取得指针变量自身地址，类型为 int **。

声明中的 int *ptr 把 ptr 声明为指针变量。表达式中的 *ptr 则是通过指针访问目标对象。指针必须事先指向有效且符合读写要求的对象。

C 调用时复制实参的值。整数形参收到整数副本，指针形参收到地址副本。函数通过地址副本可以访问调用方的原对象。

教师完整例在 next-day-demo/D21-pointer-arguments.c。已有函数实际定义如下。

```c
#include <stdio.h>

void print_number(int number)
{
    printf("number=%d\n", number);
}

void write_number(int *address)
{
    *address = 37;
}
```

四次调用分别为 print_number(value)、print_number(*ptr)、write_number(&value)、write_number(ptr)。前两次打印 10 和 20。第三次把 value 改为 37，target 仍为 20；第四次把 target 改为 37。

当前任务若采用 int b = 1，queue_pop 的 int *out 接收 &b，device_step 的事件值接收 b。device_step 的当前状态形参接收 *state，因为 state 本身的类型为 enum DeviceState *。当前学生核心需在保存修订后重新严格编译和执行原批量断言，教师示例运行不替代学生过关证据。

16:23补充。初始化或赋值先求右侧表达式的值，等号本身不取地址。假设int event=1，其所在地址为1000（示意），那么表达式event得到整数1，&event得到对象地址。int*b=1和int*b=event都把整数给指针，类型不符；int*b=&event建立对真实int对象的指向。若另一个int*p=&event，b=p复制p保存的地址。对象内容改变不会因此改变它的地址，继续通过b解引用会访问更新后的内容。单独整数常量1没有为输出参数提供可写int对象地址。
