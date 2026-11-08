# D12扩展：连续命令控制台

## 目标与边界

按L3既定顺序，把整行读取、容量确认、固定标签和命令分类串联为PC文本命令原型。连续C，替换D12未用容量，不增加日预算、不跳struct/enum/状态机。学生只写main及本题新的循环/状态分派；旧读取/分类实现由教师链接，学生不重抄。

目标文件03-code_codex/d12-command-console.c已创建为空白。头文件stdio.h、d12-line-reader.h、d12-bounded-command.h。学生声明char text[16]，调用read_complete_line(text,sizeof text)，仅LINE_READY时使用本行数据并调用bounded_command_kind。

## 已有读取接口

int read_complete_line(char *dest,int capacity)。dest指向capacity格可写数组、capacity>=2；本题使用16。输入为无内嵌NUL的文本。一次调用处理一条物理行，必要时清理超长行余部；可能阻塞等待输入或行结束/EOF。最多接受15个正文字符。成功时剥掉换行，保留结束符；末行没有换行但已确认正常EOF也可成功。

| 常量/值 | 含义与产生条件 | 本次可依赖输出 |
|---|---|---|
| LINE_READY / 1 | 整行已取得；包括空行或EOF结尾的完整末行 | dest为有效结束字符串，不含换行；只有此状态允许本题分类dest |
| LINE_END / 0 | 本次尚未读到字符就正常EOF | 没有本次文本，不能复用上次dest分类 |
| LINE_TOO_LONG / 2 | 一行超过15正文；余部已消费到换行或EOF | 本行拒绝，不解析缓冲前缀；下次调用从下一行或EOF开始 |
| LINE_IO_ERROR / -1 | 实际读取失败，流错误标志成立 | 不依赖dest内容；停止处理 |
| LINE_BAD_BUFFER / -2 | NULL缓冲或容量不足2 | 没有可解析文本；本题固定16不应发生，但入口仍处理 |

注意读取状态与分类状态是两个独立变量、不同契约，不能把读取-1解释为缺斜杠，或把读取2当STOP。LINE_*为头文件里已定义的整数宏，直接用名称比较，学生不用另写定义。

## main业务要求

- 连续处理多行。LINE_READY时输出bounded_command_kind的返回整数和换行，每行只输出一次，然后处理下一行。
- LINE_TOO_LONG输出TOO_LONG及换行，继续下一行；不分类本次缓冲。
- LINE_END正常结束main，返回0，不输出额外一行。
- LINE_IO_ERROR输出READ_ERROR及换行，main返回1。
- LINE_BAD_BUFFER输出BUFFER_ERROR及换行，main返回1。
- CMD/STOP仅打印分类2，仍继续读取，不停止控制台，也不代表硬件操作。
- 不增加提示文字，确保输出可逐行自动核对。只读一次后按状态处理，不额外fgetc，不手动补读或重复调用读取函数来判断同一行。

## 验收

输入CMD/RUN换行、CMD/换行、ROOM/RUN换行、CMD/STOP换行，关闭输入后输出1、-2、-3、2，各占一行，退出0。

输入CMD/ABCDEFGHIJKL换行再CMD/RUN换行：第一行16正文，超长，输出TOO_LONG，然后1。输入CMD/ABCDEFGHIJK换行（15正文）允许读取，命令未知，输出0。

空输入不打印、退出0。单独空行输出-1；CMD/输出-2。最后CMD/STOP无换行但正常EOF，仍输出2后结束，不重复处理旧内容。

## 教师依赖与预检

读取适配d12-line-reader.c复用week-review/review_input.c，原源未改。9组实际教师检查见d12-line-reader-validation.json，包括真实读错误（隔离临时只写流）及缓冲配置错误。这里只验证读取依赖，学生main尚未实现、控制台未通过。
