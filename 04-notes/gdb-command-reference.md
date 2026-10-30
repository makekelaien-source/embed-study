# GDB操作参考（Windows / MinGW）

本机GDB 18.1，2026-10-30整理。长期参考，保留原位。未练过的命令只供查阅，不算已经掌握。完整命令索引见同目录gdb-all-commands.txt。

## 先认清三个对象

- `.c`是源码，GCC编译产生`.exe`，`gdb.exe`是调试工具。
- `PS ...>`后输入PowerShell命令，`(gdb)`后输入GDB命令。
- 设置断点不启动程序；`run`或`start`才启动。暂停后才能单步观察。

## 1. PowerShell中编译与加载

```powershell
Set-Location 'D:\Apostgraduate\opencode\embed-study\03-code_codex'
& 'D:\embedded\mingw64\bin\gcc.exe' -g -O0 -Wall -Wextra .\d4-gdb-practice.c -o .\d4-gdb-practice.exe
& 'D:\embedded\mingw64\bin\gdb.exe' -q .\d4-gdb-practice.exe
```

`-g`生成调试信息；`-O0`关闭优化，方便按源码观察。修改源码后需重新编译；编译失败时不要把旧exe当作新版本。

## 2. 加载、启动和退出

| GDB命令 | 作用 |
|---|---|
| `file d4-gdb-practice.exe` | 加载或更换目标exe |
| `run` / `r` | 从头启动程序；已有进程时会询问是否重启 |
| `start` | 启动后临时停在main开头；该临时断点命中后删除 |
| `set args 参数` | 设置目标程序下次启动时的参数 |
| `show args` | 查看参数 |
| `continue` / `c` | 从暂停位置继续，直到断点、信号或结束 |
| `Ctrl+C` | 程序运行时请求中断，可用于查看死循环位置 |
| `quit` / `q` | 退出GDB；目标仍运行时关注确认提示 |

程序尚未启动时，`next`、`continue`会报没有运行。程序正常结束后可再次`run`，断点一般仍保留。

## 3. 设置和管理断点

| 命令示例 | 作用 |
|---|---|
| `break add` / `b add` | 在add函数处设置断点 |
| `break d4-gdb-practice.c:15` | 指定文件和行号；对照实际源码 |
| `break 15` | 在当前源码文件第15行设置断点 |
| `tbreak add` | 只命中一次的临时断点 |
| `info breakpoints` | 查看编号、位置、启用状态和条件 |
| `condition 1 right < 0` | 给1号断点添加或替换条件 |
| `condition 1` | 移除1号断点的条件，保留断点 |
| `break add if right < 0` | 创建时同时设置条件 |
| `disable 1` | 暂时禁用，保留断点 |
| `enable 1` | 重新启用 |
| `delete 1` | 删除1号断点，不删除源码 |
| `delete` | 删除全部断点，关注确认提示 |
| `clear add` | 按代码位置清除断点 |
| `ignore 1 2` | 忽略1号断点接下来的2次命中 |

断点编号以当前会话为准，不固定。重复执行`break add`可能产生多个同位置断点。`condition`中的变量必须在断点位置有定义；本练习是`left/right`，不是上一题的`a/b`。

## 4. 单步与控制执行

| 命令 | 作用 |
|---|---|
| `next` / `n` | 源码级步过调用，走到当前层后续源码位置 |
| `step` / `s` | 源码级步入，有调试信息时可进入被调用函数 |
| `finish` / `fin` | 让所选帧对应函数执行到正常返回，通常显示返回值 |
| `until 18` | 在当前调用层运行到指定行，或该帧返回 |
| `until` / `u` | 向前运行，常用于越过循环；实际停点受机器码布局影响 |
| `next 3` | 连续进行最多3个next步骤 |
| `stepi` / `si` | 指令级步入，汇编阶段再学 |
| `nexti` / `ni` | 指令级步过，汇编阶段再学 |

这些操作可能被其他断点或信号提前打断。源码一行可能有多个步骤，不能理解成每次恰好执行一条C语句。当前位置显示的源码行通常尚未执行完，尤其函数返回与调用方赋值之间要结合实际位置判断。

## 5. 查看变量和表达式

| 命令 | 作用 |
|---|---|
| `print total` / `p total` | 查看变量 |
| `print left + right` | 计算并查看表达式 |
| `print values` | 查看数组 |
| `print values[1]` | 查看一个元素 |
| `print/x total` | 十六进制显示 |
| `print/d total` | 十进制显示 |
| `print/t total` | 二进制显示 |
| `print sizeof(total)` | 查看类型大小 |
| `ptype total` | 查看类型 |
| `info locals` | 查看所选帧的局部变量 |
| `info args` | 查看所选帧的形参 |
| `display total` | 暂停时自动显示表达式，需处于有效上下文 |
| `info display` | 查看自动显示项和编号 |
| `undisplay 1` | 移除1号自动显示项，编号与断点独立 |
| `printf "total=%d\n", total` | 按格式输出 |

`printf "total"`只输出文字；查看变量用`print total`。`$1`、`$2`是GDB结果历史编号，不是C变量。表达式可以包含赋值、自增和函数调用，这些可能改变程序；日常观察优先用无副作用表达式。

## 6. 查看调用栈与其他函数的变量

| 命令 | 作用 |
|---|---|
| `backtrace` / `bt` | 查看调用链 |
| `frame 0` | 选择0号帧，通常是当前最内层执行帧 |
| `frame 1` | 选择1号帧 |
| `up` | 往调用者方向切换观察层 |
| `down` | 往被调用者方向切回观察层 |
| `info frame` | 查看所选帧详情 |

`up/down/frame`只改变查看上下文，不执行代码，不让函数返回。切换后继续单步前可先`frame 0`回到真实执行帧，减少混淆。

本题：`left/right`属于add，`total`属于main。停在`add(left=7,right=-3)`时，`up`后`print total`得到7，因为这次调用还未返回。即使`finish`显示返回4，调用方赋值是否完成仍需看后续执行位置。

## 7. 监视点：值发生变化时停

| 命令 | 作用 |
|---|---|
| `watch total` | 表达式值改变时暂停 |
| `rwatch total` | 读取时暂停，依赖平台/硬件支持 |
| `awatch total` | 读取或写入时暂停，依赖平台/硬件支持 |

`break`关注代码位置，`watch`关注值变化。局部变量必须处于有效作用域；离开作用域时相关监视点可能被删除。硬件数量与平台支持以实际诊断为准。

## 8. 源码、路径和显示

| 命令 | 作用 |
|---|---|
| `list` / `l` | 显示附近源码 |
| `list add` | 显示函数附近源码 |
| `list 文件名:行号` | 显示指定位置 |
| `info sources` | 查看已知源码文件 |
| `directory 路径` | 添加源码搜索目录 |
| `pwd` | 查看GDB工作目录 |
| `cd 路径` | 更改GDB工作目录 |
| `set pagination off` | 关闭长输出分页 |
| `show version` | 查看版本 |

## 9. 进阶功能索引

以后按具体任务学习，不要求今天执行：

- 内存与汇编：`x`、`disassemble`、`info registers`。
- 多线程：`info threads`、`thread 编号`、`thread apply all bt`。
- 异常终止：停住后先`bt`，再结合`frame`与`info locals`找原因。
- 批处理：`source 命令文件`、`commands 断点号`与`end`、启动参数`-batch -ex`。
- 改变被调试状态：`set variable`、`call`、`return`、`jump`。这些不是纯查看，不把人为改出的结果当作正常执行证据；`finish`实际执行到返回，而`return`可强制返回，两者不同。
- 进程管理：`attach`、`detach`、`kill`。涉及选定进程的运行状态，使用前先查详细帮助。
- 嵌入式：`target remote`、`monitor`、`load`，需要对应服务器与正确硬件目标，上板阶段再学。

## 10. 获取所有命令与详细帮助

```text
help
help all
help break
help condition
help print
help next
apropos breakpoint
```

`help all`是本版本全部命令的简要索引，已导出同目录txt。`help 命令`查具体语法；`apropos 关键词`搜索说明。缩写必须唯一；`nex`可能与nexti歧义，明确别名`n`则可用。

## 11. 练习路线

从尚未运行的状态，只停在负数调用：

```text
break add if right < 0
run
print left
print right
print left + right
up
print total
down
finish
```

从main开始观察第一次调用：

```text
start
break add
continue
print left + right
finish
print total
next
print total
```

如果会话已有断点，先`info breakpoints`核对；多余的无条件断点会提前暂停。每次进入add仍可能命中，若想跑完先禁用相应断点，再continue。

## 12. 本次实际卡点

1. 只设断点，没有启动程序。
2. 对已经删除的临时断点添加条件。
3. 把另一份程序的参数名套进当前程序。
4. 重复设置断点，不知道旧断点仍生效。
5. 把printf文字当作查看变量。
6. 在add上下文寻找main的局部变量。
7. 把切换观察帧当作执行函数返回。
8. 把候选计算值与函数真正return的值混在一起。

## 官方参考

- [完整手册](https://sourceware.org/gdb/current/onlinedocs/gdb.html/)
- [继续与单步](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Continuing-and-Stepping.html)
- [断点](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Breakpoints.html)
- [调用栈](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Stack.html)

新功能是否适用于本机，以本机help与实际运行结果为准。
