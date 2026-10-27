# 学习记忆（长期）

> 每次会话涉及嵌入式学习时先读本文件；记录每日学习后更新「当前状态」。

## 基本信息
- 背景：建筑学本科，编程与电子基础≈0，转行自学嵌入式
- 目标岗位：嵌入式软件工程师（非硬件/芯片）
- 差异化故事线：智能建筑 / 楼宇自动化 / 建筑物联网（利用建筑背景）
- 求职优先级：大公司嵌入式软件岗 → 中小公司（智能家居/智能照明/楼宇自控方向作为故事线加分项）

## 关键决策
- 跳过 51 单片机，直接学 STM32（江协科技或正点原子课程）
- 技术栈：C 语言为核心 → STM32 裸机 → FreeRTOS → ESP32/MQTT
- 2026-10-21 加入 Python 辅助线（就业加分项，不替代 C）：目标「能写工具脚本、能读懂测试代码」；阶段0 每周 2~3h，C 任务未完成则当周 Python 取消；详见总览「Python 辅助线」与逐周计划
- 简历主打项目③：智能照明/暖通控制器原型（STM32 + FreeRTOS + PWM + MQTT + OTA + 低功耗）
- 学习起点：2026-10-21（Day 1），全职节奏约 40h/周；兼职（15h/周）则时间 ×2.5
- 硬件预算 500~700 元：Arduino Uno 起步包、STM32F103C8T6 最小系统板 + ST-Link、ESP32、面包板/杜邦线、TTL 串口模块、（可选）逻辑分析仪
- 2026-10-22 用户明确：硬件不急。真实动机项目是「用 Arduino 制作特殊磁场」，到时按项目需求选型下单；当前专注编程训练
- 目录/文件名一律英文（用户在终端手打路径省输入法切换），文件正文中文；2026-10-20 已把 `D:\嵌入式学习` 整体复制为 `D:\Apostgraduate\opencode\embed-study`（旧目录待用户关闭 VS Code / 重启 OpenCode 后手动删除）
- 2026-10-22 用户明确每日教学流程（已写入全局 AGENTS.md）：先学后练——练习前先在 04-notes 写好当天知识讲义并在对话里逐行带读，确认能复述后才给练习；练习只用讲义教过的语法
- 踩坑记录（2026-10-22）：中文文件名让 go.bat 找不到文件、cmd 编码错乱，改 ASCII 名后正常；PowerShell 跑当前目录程序要 `.\` 前缀。教训：一切会被终端/脚本处理的名字（文件名、路径示例、命令）一律英文

## 当前状态
- 阶段：阶段0 进行中（Day 0-6 完成：环境 + hello.c；Day 1 变量/数据类型/printf/scanf；Day 2 运算符/类型转换/比较逻辑；Day 3 if/else/else if + && \|\| 组合；Day 4 switch/break/default + for 循环；Day 5 while/do-while/嵌套循环/break/continue；Day 6 猜数字游戏 + 1~100 素数表；Day 7 函数基础：定义/参数/返回值/void/先定义后使用/传值复印件/作用域——控制流已清零，仅剩 Fibonacci 并入本周短练习；本周（W2）：函数收尾 → 数组 → 冒泡排序 → 杨辉三角）
- 本周目标：见 01-plans\weeks-01-12-plan.md（W1 的 C 内容全部完成且控制流练习提前做完，进度超前约 1 周；本周函数与数组，检验项=独立写冒泡排序并逐行解释；硬件按用户决定暂缓，不再催下单）
- 累计学习天数：8（Day 0-7）
- 最近日志：2026-10-27（Day 7，✅ 已完成）
- 已知薄弱点：中文标点混入代码（最高频）、scanf 忘加 &（Day 5 一天踩 4 次，与中文标点并列最高频）、if 条件里 `=` 写成 `==` 混用（Day 5 踩 3 次，会让 if 判断完全失效，检查时要优先看这处）、while 后多写 `;` 造成死循环、曾把 % 占位符当变量名（已纠正：按逗号顺序填）、scanf 占位符与类型不匹配（int 写成 %f，Day 2 新踩，已纠正）、整数除法陷阱、程序不退出导致 exe 占用重编译失败；数学定义类概念（如素数）理解吃力，需先类比再代码；已会自行修复引号/注释/未初始化/return/占用类报错
- 已掌握：强转只贴近相邻操作数（(float)a/b ≠ (float)(a/b)）、==/&&/||/i++/i+=、int 截断小数不四舍五入、if/else/else if 分档（先严格后宽松）、判奇数用 n%2 != 0、switch/break/default（穿透会执行后面所有 case）、for 三段式、for+if 组合（i%7==0）、scanf 会覆盖它读入的变量、`x = x++` 是空操作（++ 单独用）、while（次数未知）/do-while（至少一次，菜单）、while(1)+哨兵值 break 处理不定个数输入、嵌套循环（外层 1 步=内层一整轮）、break 结束整个循环 / continue 跳过本轮剩余、循环里先检查特殊值再累加、素数试除法（j 从 2 起，循环外判 i == j：内层跑到 j==i 没报警即素数）、break/continue 只绑定最里层循环（括号房间规则）——Day 6 已能自行修好素数程序并复述 9 的判定过程；函数四件套：定义先于使用（编译器从上往下读）、int/void = 发货标签、return 是唯一出货口、「寄了才接，不寄不接」（void 不接返回值、必须在内部留痕迹）、传值=发复印件（改复印件不动原件，要生效须 `v = try_double(v);` 接住）——Day 7 ex3 预测与实跑一致
- 卡点处理记录：Day 3 拆散的 ex2 五档链已于 Day 4 修好并测试通过；d4-ex4 酷暑阈值写成 >=35（应为 >=40），用户判断「数值上的事没必要」选择不改——语法结构问题照常纠正，纯数值阈值偏差尊重用户判断；Day 5 素数判断（d5-final.c）逻辑错 2 处（循环从 i=1 起、"是素数"印在循环内），已带讲「循环后 i==num 判断」模式；Day 6 复验通过——d6-primes.c 由用户自行修好（i == j、删多余 break），标准答案 d5-final-ans.c / d6-primes-ans.c 已写好验证，d5-final.c 修正列为选做；d6-guess.c 两处小风格问题（while 应为 if、printf 缺 \n）用户选择不改；Day 7 int/void 与 return 关系混淆，用 d7-demo3 并排对比（int area_calc vs void area_print）+「寄了才接」规则讲通，复印件陷阱用打印店类比 + ex3b 实验（v = try_double(v) 跑出 20）讲通

## 开发环境（2026-10-20 就绪）
- GCC 工具链：winlibs 便携版，装于 `D:\embedded\mingw64`（已加入用户 PATH）
  - gcc 16.2.0 / GNU Make 4.4.1（mingw32-make）/ gdb 18.1，编译运行验证通过
  - 注意：MinGW 不能放在含空格路径（`D:\working software` 下会链接失败），故放 `D:\embedded`；今后所有嵌入式工具链路径一律避免空格
  - 安装包备份：`D:\working software\embedded\winlibs-gcc.zip`（SHA256 已校验）
- VS Code 1.131（`code` 在 PATH）+ C/C++ 扩展 ms-vscode.cpptools 1.34.4
- Git 2.55：`D:\working software\git\Git\cmd\git.exe`（PATH 正常）
- Python 3.12.10：`D:\working software\python\python.exe`（PATH 正常）
- 待装（约第 4~5 周）：STM32CubeIDE、CH340 驱动；CMake 便携版推迟到工程化阶段前

## 文件索引
- 总计划：`D:\Apostgraduate\opencode\embed-study\01-plans\overview-40week-plan.md`
- 近期细计划：`D:\Apostgraduate\opencode\embed-study\01-plans\weeks-01-12-plan.md`
- 每日日志：`D:\Apostgraduate\opencode\embed-study\02-logs\YYYY-MM-DD.md`（模板 template-daily-log.md 在同目录）
- 代码练习：`03-code`（含快捷编译脚本 go.bat，PowerShell 里要写 `.\go 名字`，必须带 `.\` 前缀）/ 笔记：`04-notes` / 项目：`05-projects` / 求职：`06-job`
