# D7错误稿与操作回执补充（聊天转录）

> 下列是学生已提交聊天内容的转录，保留错误以便复习；不是磁盘原字节备份，也不是正确参考。最终源文件及四份new_alert原字节错误稿另列入学习册。完整提示/测试结果见原课堂日志。

## C查找首稿：数组类型、提前返回、漏返回

```c
#include <stdio.h>
int find_char_index(const char *text, int capacity, char target);
int main(void){
    int group[8] = "AB;CD";
    int capacity = sizeof(group) / sizeof(group[0]);
    int target = ';';
    printf("%d",find_char_index(group,capacity,target));
}
int find_char_index(const char *text, int capacity, char target){
    for(int i=0;i<capacity;i++){
        if(text[i]==target){
            return i;
        }else return -1;
    }
}
```

第二稿学生将数组改char、未匹配return -1移循环外，但尚无结束符停止；第三稿循环如下，错误地把空字符当命中下标，且scanf("%c",target)缺地址：

```c
int find_char_index(const char *text, int capacity, char target){
    for(int i=0;i<capacity;i++){
        if(text[i]==target || text[i]=='\0'){
            return i;
        }
    }
    return -1;
}
```

最终稿在单独分支将结束符返回-1，输入地址改&target，十函数例+三有效输入通过。输入失败返回尚未处理。

## Python函数首稿：漏冒号

```python
def celsius_to_offset(value)
    return value - 20

answer = celsius_to_offset(25)
print(answer)
```

教师示范定义行加冒号，学生改后三组通过。

## 列表函数首稿：计数未初始化、循环变量复用

```python
def count_at_(values,threshold):
    for values in values:
        if values >= threshold:
            a += 1
    return a
answer = count_at_([2,5,5,9],5)
print(answer)
```

同名for合法，但复用了列表名字，容易混淆；真正运行首错为a未初始化。

## 筛选列表前两稿：元素值与下标

```python
def keep_at_least(values,threshold):
    selected = []
    for item in values:
        if values[i] >= threshold:
            selected.append(values[i])
    return selected
```

i未定义。第二稿将两个values[i]改values[item]，item依次2/5/5/9，把值5当下标越界；最终直接比较item、append(item)才正确。

## 安全状态首稿：打印不是返回

```python
def safe(sample):
    if "limit" in sample:
        print(status_when_complete(sample))
    else:
        print("NO_LIMIT")
sample = {"teperature": 26}
safe(sample)
```

旧依赖status_when_complete返回字符串，外层safe只打印、没有return，四组实际返回None。学生修return后四组通过；用户明确保留teperature拼写，不再要求返工。

## 字典筛选前两稿：只返回第一个与零轮无返回

```python
def high_locations(readings,threshold):
    for item in readings:
        if readings[item] >= threshold:
            return item
```

第二稿新增结果列表却仍将return放if内：

```python
def high_locations(readings,threshold):
    sum = []
    for item in readings:
        if readings[item] >= threshold:
            sum.append(item)
            return sum
```

第三稿return移循环外后五例教师通过。

## new_alert第四稿：误删除所有旧位置（未运行）

```python
def new_alert(previous,current,threshold):
    group2 = high_locations(current,threshold)
    for item in previous:
        if item not in group2 and previous[item] < threshold:
            group2.append(item)
        if item in group2:
            group2.remove(item)
    return group2
```

学生随后中断要求重新说明目的，此稿没有实际工具测试，不伪造运行结果。初稿/第二/第三/第五稿的完整原字节在archive文件，最终稿原文件为教师验证14例通过版本。教师完整澄清“报警状态”与“新增提醒”后才继续；需求不清的责任不能算学生独立理解失败。

## pdb学生实际回执（按消息合并）

```text
> d:\apostgraduate\opencode\embed-study\03-code_codex\d7-python-list-function.py(1)<module>()
-> def count_at_(values,threshold):
(Pdb) b 5
Breakpoint 1 at d:\apostgraduate\opencode\embed-study\03-code_codex\d7-python-list-function.py:5
(Pdb) c
> d:\apostgraduate\opencode\embed-study\03-code_codex\d7-python-list-function.py(5)count_at_()
-> a += 1
(Pdb) p value
5
(Pdb) p a
0
(Pdb) n
> d:\apostgraduate\opencode\embed-study\03-code_codex\d7-python-list-function.py(3)count_at_()
-> for value in values :
(Pdb) p a
1
(Pdb) c
> d:\apostgraduate\opencode\embed-study\03-code_codex\d7-python-list-function.py(5)count_at_()
-> a += 1
(Pdb) p value
5
(Pdb) p a
1
(Pdb) c
3
The program finished and will be restarted
> d:\apostgraduate\opencode\embed-study\03-code_codex\d7-python-list-function.py(1)<module>()
-> def count_at_(values,threshold):
(Pdb) print a
*** SyntaxError: Missing parentheses in call to 'print'. Did you mean print(...)?
(Pdb) q
PS D:\Apostgraduate\opencode\embed-study\03-code_codex>
```

disable 1只有教师指令、没有学生回执，不补进实际执行序列。以上是指导下操作，不算学生独立诊断。
