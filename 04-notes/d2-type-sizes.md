# D2基础实测：sizeof、字节与数值

## 目标与前置

接续位/字节与非负位宽知识；新点是sizeof运算符（查占用字节数）及配套printf格式%zu。当前平台字节8位由教师实测CHAR_BIT确认；不把本机类型大小说成C所有平台固定值。计划20–30min含示例、学生小程序和解释，实际计时，提前通过不填满。

## 带读

sizeof(int)查询int类型大小，以字节为单位，打印写printf("%zu\n", sizeof(int));。sizeof是运算符而非普通函数，不需要学生实现。sizeof(variable)查变量类型大小，变量值从1改为256不会改变其类型或占用大小；和“数值256的二进制最短需要9位”是两个问题。

教师可代跑当前平台int/float/char及CHAR_BIT，观测值与语言保证区分。sizeof(char)为1是C规则，1字节具体几位由CHAR_BIT描述；本项目平台为8位。当前int4字节就占32位，不在本课立即展开补码或所有类型取值范围。

## 学生任务

空白03-code_codex/d2-type-sizes.c，学生定义int number=256，分别打印number的值、sizeof(number)、sizeof(int)、sizeof(float)、sizeof(char)，每项一行。值使用%d，sizeof结果用%zu。助手代编译并将number改1作临时副本对照，不要求学生机械重跑。

当前教师示例只给int查询一行，不代写学生完整任务。验收学生能区分值与类型大小、字节与位数；具体输出取当前实测，不要求背所有机器大小。以实际学生代码/解释升级，约11-04新情境复测待做。
