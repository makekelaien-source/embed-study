# D4补充单元：GDB暂停、单步与变量

目标：在今日实际库存程序中观察执行位置及库存状态；前置为构建与变量/循环。工具块45分钟容量，不把教师编译/测试算学习。

新概念：调试器可暂停被调试程序；当前位置显示的语句通常尚未执行。第一步只启动GDB并start，随后才教next与print，不一次铺开命令。

教师准备：保持学生源不变，GCC -std=c11 -g -O0 -Wall -Wextra -pedantic -finput-charset=UTF-8 -fexec-charset=UTF-8构建03-code_codex/d4-stock-debug.exe；仍有学生明确保留的least_positon未使用警告。

教师实际验证：gdb -q -batch -ex start -ex next -ex "print storeage"，停止main第9行初始化之前；next后停第10行，print storeage输出5。退出码0。只记教师环境验证，不记学生调试能力。

学生入口：PowerShell运行D:/embedded/mingw64/bin/gdb.exe -q并加载debug exe；出现(gdb)后start。学生提交实际停止位置，再教next与print。后续观察接受/拒绝路径与库存承接；以学生真实操作、解释与迁移验收。未知分钟保持未知，不反复口问已会基础。

## 函数断点
- break manipulate：设函数断点；continue：恢复执行到下一断点或结束。学生先观察停在哪个函数，再用print a/print b看当前函数形参，不能把此时局部a混成main的storeage。该单元分步发布，未执行不记能力。

## 返回值与更新位置
- print a+b查看表达式；finish运行完当前函数并返回调用处，观察返回值。首次调用实际和8/返回1。返回main后先print storeage，再next定位更新语句，强调返回标志不等于库存值。

## 条件断点
- 当前学生断点编号2：condition 2 a + b < 0；continue。断点仍在manipulate，仅条件为真时暂停。教师已实际验证该条件在当前数组命中a=4/b=-8，无需机械步进全部循环。先观察参数，再finish与main库存是否保留。

## 查看调用方变量
- printf打印格式化文字，print查看变量/表达式。total属于main局部变量，left/right属于add。up只把观察栈帧切到调用者，不执行代码、不退出函数。教师实际验证负数调用处up后print total=7；add尚未返回，最后减3尚未赋回。当前学生先练up与print。
