# D8综合题：静音后的新增报警报告

> 学生要求先不学新内容，综合最近几日已学Python。旧函数由教师提供，本题不学新语法、不读写文件。预留原测试复盘容量40分钟，非实际学时；pdb暂缓，算法/后续测试尚未发生，不删除预算。

## 文件与依赖

学生文件：03-code_codex/d8-alert-report.py（已创建空白，既有内容不得覆盖）。同目录d8_alert_tools.py提供new_alert(previous,current,threshold)，返回当前达到阈值且上次未报警/缺上次记录的区域名列表，顺序为current字典顺序，持续报警不重复。学生调用已有函数，不复制或重写旧报警逻辑。

## 任务

定义prepare_report(previous,current,threshold,muted)。previous/current为区域名到温度的字典；threshold为数值；muted是本次不通知的区域名列表。调用旧new_alert得到新增候选，排除muted中的区域，保持其余顺序。静音只影响是否通知，不修改温度/报警状态。返回字典，准确包含以下键：

- notify：最终通知的区域名列表。
- count：最终通知数量（静音后）。
- path：当前脚本所在文件夹/reports/alert.csv的Path对象，不是工作目录下路径。

字典的值在本题分别保存列表、整数、路径对象；path就是前面练习的target这一类对象，不增加新语法。函数内部不打印，不修改三个输入容器，不要求输入验证、真实文件存在或写CSV。代码外准备样本、调用函数并接住返回字典，依次打印notify、count、path（三个print即可，输出排版不作核心阻塞）。

## 样本与验收

previous={"east":35,"west":18,"north":10}
current={"east":36,"west":30,"north":32,"south":31}
threshold=30
muted=["north"]

最终notify为['west','south']，count为2；path为D:/Apostgraduate/opencode/embed-study/03-code_codex/reports/alert.csv。east持续报警不属新增；west恰达阈值；north新增但静音；south缺上次记录且当前达阈值。

教师后续批测：双空返回[]/0；静音覆盖全部新增时返回[]/0；无静音时返回全部新增；不在候选中的静音名不影响结果；输入不变；函数无打印；从两个工作目录启动path保持相同。学生只写一版，不机械换数组或重抄函数。

## 教师准备证据

出题前已运行既有模块：标准样本新增候选['west','north','south']、双空候选[]均符合预期。学生prepare_report尚未实现、未测试，不计通过。参考答案未写入题面。
