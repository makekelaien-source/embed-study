# D7 讲义：函数（W3 第 1 天）

> 类比先行：函数就像建筑里的「标准详图」。一面墙的做法（砌砖-抹灰-贴砖）画成一张标准详图，
> 整栋楼几十处墙面都直接引用它，不用每处重新画一遍。
> 程序里凡是「同样的事要做很多次」，就打包成一个函数，写一次，到处调用。

你已经用了 6 天的 main() 本身就是一个函数——程序从它开始执行。
printf、scanf 也是别人写好的函数，你只负责「调用」。今天学的是：自己写函数。

---

## 1. 函数长什么样（定义）

```c
#include <stdio.h>

int add(int a, int b)      // <- 这一行叫「函数头」
{                          // <- 函数体开始
    int sum = a + b;
    return sum;            // <- 把结果交出去，函数到此结束
}                          // <- 函数体结束

int main(void)
{
    int x = add(3, 5);     // 调用：把 3 和 5 递进去
    printf("x = %d\n", x); // 打印 x = 8
    return 0;
}
```

逐行拆：

- `int add(int a, int b)`：
  - 第一个 `int` = 这个函数**交出来的结果**是什么类型（这里是整数）
  - `add` = 函数名，自己起的，规则同变量名（英文、数字、下划线，不能以数字开头）
  - 括号里的 `int a, int b` = **参数**：外面递进来的东西，先给它们起名字接住
- `return sum;`：把 sum 交给调用者，**这一行一执行，函数立刻结束**，后面的代码不跑
- `add(3, 5)`：调用。3 复制给 a，5 复制给 b，函数跑完把结果填到这个位置

类比：add 是一台榨汁机。参数 = 投进去的水果；return = 出来的果汁。
投进去的是**副本**（见第 4 节），出来的是新东西。

## 2. 四种组合（参数 / 返回值 可有可无）

| 类型 | 写法 | 例子 |
|---|---|---|
| 有参数有返回 | `int add(int a, int b)` | 上面的 add |
| 有参数无返回 | `void show(int n)` | 只干活（比如打印），不交结果 |
| 无参数有返回 | `int get_year(void)` | 不递东西，只交一个结果 |
| 无参数无返回 | `void hello(void)` | 打招呼这种纯动作 |

`void` = 「空」，表示这一项没有。无返回就写 `void`，且函数里不用 `return 值;`。

```c
void hello(void)
{
    printf("hello!\n");   // 没有 return 值, 但函数结束自然返回
}

int main(void)
{
    hello();              // 调用时括号里什么都不写
    return 0;
}
```

## 3. 先定义，后使用

C 语言要求：函数必须**写在调用它的代码之前**（main 通常写在最后）。
就像施工图：先有详图，别处才能引用它。引用一张还没画的图，编译器报错。

```c
#include <stdio.h>

void hello(void) { printf("hi\n"); }   // 先定义

int main(void)
{
    hello();                           // 后调用, 正常
    return 0;
}
```

## 4. 参数是「复制一份」递进去的（值传递）

```c
#include <stdio.h>

void try_change(int n)
{
    n = 100;          // 只改了副本, 外面的 n 不受影响
}

int main(void)
{
    int a = 5;
    try_change(a);
    printf("a = %d\n", a);   // a 还是 5 !
    return 0;
}
```

类比：你把文件的**复印件**递给同事修改，原件还是原样。
想让函数改原件？那是 W4 指针的内容，今天不用管，记住「递进去的是复印件」即可。

## 5. 作用域：变量只活在它的「括号房间」里

你已会「括号房间」规则（break/continue 只绑定最里层）。变量同理：

- 函数里定义的变量 = 局部变量，**只在这个函数的 {} 里存在**，出了门就销毁
- 两个函数里可以各有一个同名变量，互不干扰（两个房间各放一台打印机）

```c
#include <stdio.h>

void f1(void)
{
    int n = 1;        // f1 房间的 n
    printf("f1: n = %d\n", n);
}

void f2(void)
{
    int n = 99;       // f2 房间的 n, 和 f1 的 n 毫无关系
    printf("f2: n = %d\n", n);
}

int main(void)
{
    int n = 7;        // main 房间的 n
    f1();
    f2();
    printf("main: n = %d\n", n);   // 还是 7
    return 0;
}
```

## 6. return 的两个细节

1. `return` 后面没东西执行到它，函数就结束：

```c
int abs_value(int n)
{
    if (n < 0) {
        return -n;    // 负数走这里, 函数直接结束
    }
    return n;         // 否则走这里
}
```

2. 声明了返回 int，就必须每条路都 `return 整数;`，否则结果不可预测。

---

## 今天只准用这些语法

main、函数定义（四种组合）、参数、return、void、if、局部变量、printf/scanf。
（循环你已会，练习里可以用。）
