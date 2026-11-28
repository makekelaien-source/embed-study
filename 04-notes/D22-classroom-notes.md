# D22｜实授内容与易错点

## 本日路线与结果

第一阶段 L6。文本命令分类后变为设备事件，事件入队，再由消费函数更新设备状态。学生只写 submit_command 与测试入口。旧解析器、环形队列、状态机和批量消费复用既有代码。
原计划300分钟是容量，实际时长见学习册导读。日终新统计接入题未做，保留空白目标。

## 指针与构建复习

int received=-1; int *p=&received; 出队形参 int *out 需要地址，实参 p 正确。通过 *out 写入会修改 received，指针 p 仍指向它。学生独立选 p，经原实现和指向提示后确认写入对象。
gcc 输入 .o 文件并组合成可执行文件是链接阶段。学生独立指出漏 run-events.o 导致 undefined reference to run_events，补相应对象能提供函数定义。

## 文字、事件与设备状态

command_kind 的输入为有效终止字符串或 NULL。精确 RUN 返回1，STOP返回2，未知返回0，NULL返回-1。RUNx、空串、大小写或尾部多字符不满足精确匹配。
外部字符串 "RUN" 映射事件 START；外部 "STOP" 映射事件 STOP。状态 RUN 描述正在运行。RUN 的枚举值2与事件 STOP 的值2重合，给 queue_push 传 RUN 虽可编译却会产生停止事件。这是学生首稿的功能错误。
submit_command 返回 SUBMIT_OK(0) 表示事件入队成功；SUBMIT_INVALID(1) 表示文本无效，原队列所有字段和槽值保持；SUBMIT_FULL(2) 表示合法命令因满队列未入队，原队列保持。满队列收到 RUNx 仍是 INVALID。设备状态在消费阶段更新。
count记录已有项数，0为空，QUEUE_CAPACITY为满。tail为下次写入下标，回绕到0不能单独说明空或满。

## 状态机

状态 BOOT 为等待初始化，IDLE为空闲就绪，RUN为运行，SAFE为故障安全状态。事件 READY为初始化完成，START为启动请求，STOP为停止请求，FAULT为故障，RESET为复位。
BOOT+READY→IDLE；IDLE+START→RUN；RUN+STOP→IDLE；任意状态+FAULT→SAFE；SAFE+RESET→BOOT；其余组合保持当前状态。
device_step只算下一状态，返回值需要调用者写回。state=device_step(state,START)先复制当前状态进入函数，再把返回的新状态赋给state。
连续事件必须把上一轮结果传给下一轮。SAFE收到START仍SAFE；恢复流程为RESET→BOOT，READY→IDLE，START→RUN。
device_consume_all从队列取事件并处理，取过至少一项返回QUEUE_OK，即使状态保持原值。开始即空返回QUEUE_EMPTY。学生能解释SAFE消费START后队列空、状态SAFE，而返回OK是因为实际取到了事件。

## 断言与测试时机

assert(条件)来自assert.h，启用时条件为真继续，为假报告位置并终止，后续断言不执行。正常无输出是预期。
一次启动停止的四个检查点为提交RUN后count1/IDLE，消费后count0/RUN，提交STOP后count1/RUN，再消费后count0/IDLE。只看最后IDLE可能漏掉从未启动的错误。
学生原稿将 RUN/STOP 枚举传给需要字符串的接口，严格编译报类型错误；两处只写 device_consume_all 函数名，没有参数括号，无法执行消费。修正为字符串和真实调用后原12条断言通过。
双设备各有队列与状态，A从IDLE、B从SAFE开始。各提交RUN后，只消费A应A空/RUN而B一项/SAFE；再消费B应B空/SAFE且A保持。学生首稿末次错误期望qb.count1，运行停在该断言。改0后20条断言通过。
关闭断言使用GCC -DNDEBUG，会让assert内表达式也不执行。教师例count=0; assert(++count==1);输出：启用1，关闭0。把有副作用的调用放在断言外，先保存返回值再检查。学生已经完成四处拆分。
submit_command返回enum SubmitResult，device_consume_all返回enum QueueResult。学生起初四个接收变量都用SubmitResult，触发enum-conversion和enum-compare。修正消费结果类型后原20条通过。
非法命令错误版先塞START再返回INVALID，返回值检查能通过，提交后count==0断言能抓住它。该检查点由学生选择，教师实际双版本运行，正确版count0通过，错误版count1失败。

## 时间和额外空间

三事件时queue_pop调用4次，其中最后一次发现空，device_step调用3次。学生独立数对。
一般n项为n+1次出队、n次状态处理，每项常数工作，按可扩展容量分析为O(n)时间。当前队列容量3只给本实例设定了上限。
局部b/a/c被循环复用，额外存储不随n增长，O(1)额外空间。队列本身的存储单独计算。状态没有改变仍须计算事件，不减少处理次数。

## 统计接口已讲，目标尚未实现

D2旧统计算法采用-999为无效值，其余整数有效。教师原字节恢复参考文件，再将既有判断与累加封装为summarize_samples，返回SampleStats，未把教师提取计为学生新实现。
SampleStats四字段valid_count、invalid_count、sum、average。只有valid_count>0时average表示有效均值。全无效平均字段0不代表测得0度，学生正确指出先查valid_count。
新目标collect_samples(state,samples,count,out)：仅RUN统计并写回；有有效项COLLECT_OK，没有有效项COLLECT_NO_DATA；其他设备状态COLLECT_INACTIVE并保持旧out。运行中空批次也写入全零结果。输入数量非负、数组足够长、有效总和在int范围内、out有效；count0允许samples为NULL。
题目已经发出，collect-samples.c空白，学生收课时明确未做最近测试。教师统计依赖7例通过不能代表目标完成，整合后的G0待后续。

## 原代码与证据

所有学生版本、教师错误版、验证回执、旧依赖完整定义均随本日清单收入学习册。功能通过与即时口头理解分别记录，延迟迁移未通过。本日编译失败、断言失败和教师提示保留。
