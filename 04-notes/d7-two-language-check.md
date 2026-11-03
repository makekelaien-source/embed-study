# D7双题综合检查（2026-11-03学生主动要求）

> 学生明确要求一道近两天C、一道人今日Python。原每日内容覆盖已补齐、课堂未结束，用户明确要求优先于默认不回切C新题的排课规则。本次统一先C再Python，不来回穿插；预计C40分钟、Python50分钟为可调整任务容量，非已发生学时。新增两核心由学生写，现有函数教师准备，不重抄。初发H0，可查已授资料。

## C：受容量限制的字符定位

文件03-code_codex/d7-c-find-char.c为空白。接口int find_char_index(const char *text,int capacity,char target)。在最多capacity个字符范围内，从左到右找首个target下标，遇首个空字符结束；找到返回0起下标，否则-1；capacity<=0返回-1且不读text。target为普通非空字符，text指向至少capacity个可读char（capacity正时），不涉及NULL。函数不打印不改输入，不用strlen等替代目标遍历。main固定数组测试并用真实数组sizeof得到容量传入，不用scanf。

验收：char a[8]="AB;CD"、容量8、';'→2；同数组'Z'→-1；char b[6]="A0B"、容量6、'0'→1；char c[6]={'A','\0','X','Y','\0','\0'}、容量6、'X'→-1；任意有效数组、容量0→-1。教师后续加容量截断与无终止符内存边界，不先给答案；字符串长度与容量不混淆，函数内sizeof指针不可当原数组容量。

## Python：新增报警位置（两次记录比较）

文件03-code_codex/d7-python-new-alerts.py先建空白，再由教师接入学生已有high_locations原文，预检旧依赖通过。新接口new_alert_locations(previous,current,threshold)，输入均位置名到温度的字典，返回当前>=阈值且上次低于阈值或上次没有该位置的位置名列表，顺序按current遍历；持续报警不重复报，当前缺失位置不输出；不改两字典、不打印、不使用未授API。必须复用high_locations(current,threshold)获取当前报警位置，学生只写两次记录比较新增核心。

验收：previous={north:20,south:32}，current={north:31,south:35,roof:30}，阈值30→[north,roof]；previous={a:30}、current={a:31}→[]；previous={a:29}、current={a:30}→[a]；previous={}、current={}→[]。所有键在真实代码中均为字符串；阈值同为30。函数外调用并打印一例，教师代跑其他固定边界与输入不变检查。

新交付是两时刻报警状态迁移，不把换位置名当新知识；仅用已授函数/列表/字典/for/if/in/append/return，无需旧函数复制、字典.get、推导式或集合。

## Python规则完整澄清（学生16:18后要求，不改变原验收条件）

必须区分“当前报警状态”与“本次新增提醒列表”。当前温度>=threshold就处于报警状态，温度<threshold正常；持续报警仍然是报警状态，仅不重复列入本次新增列表。函数不是返回所有当前报警位置，也不表示列表外所有位置都正常。

previous/current都是{位置名:温度}字典，本题值为有效数值，无None/坏输入处理任务。用同一个传入threshold判定前后两次，等于阈值也算报警。

完整规则：
- 上次低于阈值、当前低于：不输出。
- 上次低于阈值、当前达到或超过：输出，已有位置新发生报警。
- 上次达到或超过、当前低于：不输出；这是恢复正常，本题不报告恢复。
- 上次达到或超过、当前达到或超过：不输出；当前仍报警，属于持续报警。
- 上次没有该位置、当前低于：不输出。
- 上次没有该位置、当前达到或超过：输出，首次记录即报警。
- 当前没有该位置：不判断、不输出，不把缺失当温度0。

返回按current遍历顺序排列的位置名列表，每个位置最多一次；没有新增提醒返回[]。不修改previous/current，不在函数内打印，外部调用可打印。high_locations已由教师接入，只要其实现保持不变无需学生复制。

样例A：previous north20/south32，current north31/south35/roof30，阈值30→[north,roof]。样例B：previous north30/south32、同current、阈值30→[roof]。north上次30已经报警，数值变化并不必然等于新增报警；比较的是是否跨越报警状态。

教师此前没有把状态与新增提醒明确分层，学生多轮实现方向偏差应先补齐需求理解，暂不继续改代码、不因未理解需求而追加复杂循环。
