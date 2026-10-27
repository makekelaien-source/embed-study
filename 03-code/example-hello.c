/*
 * hello.c —— 你的第一个 C 程序（Day 0 热身）
 * 编译：gcc hello.c -o hello.exe
 * 运行：.\hello.exe
 */

#include <stdio.h>  // "标准输入输出"头文件：printf/scanf 这些工具在里
                    // 类比：开工前先把工具箱搬出来，工具箱叫 stdio

int main(void)      // main 是程序的入口，电脑永远从这里的第一行开始执行
{                   // { 开始，} 结束，中间是"要做的事"
    printf("Hello, 嵌入式!\n");  // 打印一句话到屏幕；\n 表示换行
                                 // 注意：字符串用英文双引号，句尾有分号
    return 0;       // 返回 0 = 告诉系统"程序正常结束"
}

/*
 * 常见报错对照：
 * 1. 'stdio.h' file not found  → 第一行拼错或漏了 #include
 * 2. 报错里有 missing ';'       → 某行句尾分号忘了
 * 3. 中文引号 "" 会报错         → 代码里的引号、括号、分号必须用英文标点！
 * 4. undefined reference `main' → main 拼错了（写成 mian 是新手第一坑）
 */
