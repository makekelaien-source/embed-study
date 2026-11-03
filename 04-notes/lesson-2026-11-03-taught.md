# D7完整已授讲义：函数、容器、调试与综合接口

> 2026-11-03实际已授。学生代码、错误稿、教师支架全文及测试来源随同并入当天学习册；本讲义不能替代学生独立证据。课堂12:08:01–16:28:55，教师处理/行政排除。

## C复习：存储范围、文本结束与访问路径

```c
char text[6] = "A0B";
text[1] = '\0';
```

六格依次为A、空字符、B、空字符、空字符、空字符。数组容量6，文本长度1；text[2]仍为B且在数组内。若第二行写字符'0'，文本长度3。'0'是普通字符，'\0'才是空字符，结束文本不等于擦除后续存储。

```c
char word[6] = "A0B";
char *text = word;
```

word是数组；text保存首字符地址，*text和text[0]均访问同一个首字符，text[1]访问下一个字符；text不是整个数组，*text也没有变成整个数组。printf("%s",text)从地址起逐字符读到首空字符，printf("%c",*text)只显示一个字符。声明中的char *text表示指针类型，使用时*text表示解引用。

sizeof(word)在真实数组声明范围得到整个数组字节数；函数形参const char *text中的sizeof(text)得到指针大小，不能还原调用者容量。函数参数应显式传容量。课堂曾应追问提到char (*whole)[6]=&word（指向整个六字符数组的另一种指针类型），造成措辞混淆后已纠正，本次不作为要求掌握内容。

```c
char word[] = "ABC";
const char *text = word;
/* text[0] = 'X'; 被此访问类型禁止 */
word[0] = 'X'; /* 原非const数组仍可写 */
```

const char *限制通过该指针改所指字符，不等于原数组所有访问路径都只读；const int limit=30则表示普通只读对象，const不只作用于指针。

错误生命周期示例（只读诊断，未运行）：

```c
#include <stdio.h>
int *make_value(void) {
    int value = 7;
    return &value;
}
int main(void) {
    int *p = make_value();
    printf("%d", *p); /* 错误：所指普通局部对象已结束生命周期 */
    return 0;
}
```

value属于make_value，普通自动局部对象在函数返回时生命周期结束。main的p仍存在，但保存地址不能给所指对象续命；与调试命令next本身无关。Python返回列表对象的寿命按引用对象规则解释，不能照搬该C例。

## Python函数与执行路径

```python
def add_one(value):
    return value + 1

answer = add_one(4)
print(answer)
```

def后函数名和形参，行末冒号；缩进为函数体，参数不写C式int。return把结果交回调用者并结束当前函数；print负责显示。调用不接返回值，不会自动把结果写回原标量变量。Python函数正常到末尾而没有执行return，自动返回None；None不是0，不是未定义变量。

```python
def show_offset(value):
    print(value - 20)

answer = show_offset(25)
print(answer)
```

输出5和None。内层函数返回字符串，外层只print它也不会自动继续返回给更外层；要return 内层调用结果。

计数器在循环前初始化，函数的最终return要依需求放在正确位置：要遍历全部元素就不能第一轮直接return。return在for体内遇空容器不会执行，函数可能到末尾返回None；变量a=0不等于函数已经返回0。

## 列表、循环变量与字典

```python
values = [12, 8, 15, 0]
for value in values:
    print(value)
print(len(values))
```

列表[]、0起下标、len为元素数量，空列表遍历0次。for与in之间是自己起的循环变量名，不需提前声明；遍历列表时每轮得到元素值而非下标。value/item/temperature不具有内建特别含义。已经取出item数字后，不要再用values[item]把该数字当下标。Python名字需合法，不以数字开头、不含空格、不用关键字。

字典保存键到值的关联，{}为空字典，{"temperature":26,"limit":30}为两字段记录；名称sample/readings不决定类型。

```python
sample = {"temperature": 26, "limit": 30}
sample["temperature"] = 33
for field in sample:
    print(field, sample[field])
```

字典默认遍历得到键，sample[field]再取对应值。列表按位置取值，字典按键取值；函数可以接收字典、返回位置名列表，两种容器不需同类型。

```python
sample = {"temperature": 26}
if "limit" in sample:
    print(sample["limit"])
else:
    print("NO_LIMIT")
```

缺失键直接读取会KeyError，in检查键存在，not in检查键不存在；键存在且值0仍是有效字段。列表的in/not in检查元素存在/不存在。条件连接用and，&是按位运算；判断字符串位置名是否在候选列表，不应把温度数字拿去查位置名。

## 修改对象、重新绑定与复制

```python
first = [1, 2]
second = first
second[0] = 9
print(first)  # [9, 2]
second = [7]
print(first)  # [9, 2]
print(second) # [7]
```

两个名字最初引用同一列表，修改元素能彼此看到；second=[7]只重新绑定second，不撤销旧列表里9的修改。

```python
def change_first(data):
    data[0] = 9
def rebind(data):
    data = [7]
numbers = [1, 2]
change_first(numbers)
rebind(numbers)
print(numbers) # [9, 2]
```

函数参数修改同一列表元素会影响调用者，局部参数重新绑定则不改调用者名字所关联的列表。before=values仍是同一列表，不能独立保留修改前内容；当前扁平数字列表使用before=values.copy()，values==before比较内容，得到True/False。本次不展开嵌套深浅复制。

```python
values = [1, 2]
result = values.append(3)
print(values) # [1, 2, 3]
print(result) # None
```

append把元素加到原列表末尾，返回None。values=values.append(3)会把名字values重新绑定为None。构造新列表并return列表的自定义函数与append返回规则不同，必须看调用的具体契约。

remove(value)删除列表首个匹配值、修改列表、返回None；不存在会ValueError，必要时先用in检查。[2,5,5,9]删除5后为[2,5,9]。不要把返回值赋回列表名。遍历previous字典而修改独立候选列表group2是可行的；遍历同一列表时删除可能漏过后续元素。

## 测试与pdb实际过程

先按需求确定预期，再运行比较。学生为>=误写>自行选[5,5,5,7,9,1]/阈值5，预期正确5、错误2，教师实跑吻合。只检查返回计数不能发现输入被改；copy前后比较支架原版3/True、教师植入修改版3/False通过。

Python -m pdb启动调试。箭头指当前将执行、尚未执行的行。学生实际b 5、c停a+=1，p value=5、p a=0；n执行加一，停回第3行for，p a=1；c再次停5行，当前第二个5、a=1；后续c打印3并自动重启回module第1行。print a报Python3缺括号语法错，q已回PowerShell。disable 1无回执，不声称已执行。

b断点、c继续、n=next、p查看表达式、q退出；n遇调用通常不进入被调用函数内部。p a是调试器命令，print(a)是Python语法；程序重启停module且函数未调用时，不能查看尚不存在的函数局部a。

## 周复习与综合题的需求边界

C值传递：adjust(reading)返回13但不保存时，reading仍10；reading=adjust(reading)才写回13。全负数最大值初值0会错误留0，非空列表可用首元素初始化。编译失败后旧exe仍可能存在，旧程序能运行不能验证新源码，先处理第一条有效GCC错误、重新编译成功再验证。相邻访问values[i]/values[i+1]，四元素时i最大2。

C综合find_char_index只查capacity范围且遇首空字符结束；target为非空普通字符。找到目标返回下标，遇结束符代表没找到而非返回其下标；scanf写字符须&target，本次最终只测有效输入，不宣称失败处理完成。

Python新增报警完整六格规则见d7-two-language-check。当前温度>=阈值就报警；函数只返回本次新增提醒，持续报警仍是报警状态但不重复列入。上次正常或缺记录、当前报警才加入；恢复、正常持续、当前缺记录不输出。键和值、阈值等号、返回列表和保持输入均属于验收，不靠某一个样例通过认定全部正确。
