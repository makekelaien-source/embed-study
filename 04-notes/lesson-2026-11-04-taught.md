# D8完整已授讲义：模块、路径、调用栈与导入行为

> 本文只记录实际讲过的内容。旧报警函数由教师复用；配置核查核心由学生写，字典列表append用法曾获H2提示。新主线仍为Python辅助轨道L3；文件读写尚未授课。

## 1. 字典中的键、值与列表

```python
data = {"east": 18, "west": 31}
for place in data:
    print(place, data[place])
```

默认遍历字典取得键，data[place]才按键取值。键名字的字符串与保存字符串的变量分开：

```python
data = {"east": 18, "name": 99}
name = "east"
print(data[name])      # 18：先求变量name的值
print(data["name"])    # 99：直接用文字name查键
```

name='east'不会改字典中的'name':99。学生本题初答99/KeyError，替换步骤补讲后自述审题疏忽；不能据口头明白记独立闭环。

字典的值也能保存列表，先按键取列表再append：

```python
groups = {"ready": [], "waiting": []}
groups["ready"].append("sensor_a")
```

结果为{'ready':['sensor_a'],'waiting':[]}。append修改原列表，返回None：

```python
report = {"changed": []}
saved = report["changed"].append("fan")
print(report["changed"])  # ['fan']
print(saved)              # None
saved = report["changed"] # 此时直接取列表，得到['fan']
```

不能把append返回值赋回保存列表的名字或字典项，否则会把该名字/项重新绑定为None。复盘首答fan/键值对错误，补讲后直接取列表对照正确。

## 2. 函数返回链和打印

```python
def read_temperature(data):
    return data["east"]

def report(data):
    print(read_temperature(data))

result = report({"east": 18})
print(result)
```

输出18/None。内层返回18给外层print，但外层没return，默认返回None，result实际接住None。将report内的print改成return后，两个函数只传值、最后print才输出一行18。return 'east'交出字符串，return data['east']交出对应数字，return data交出整个字典。

Python的函数局部名字与外层同名变量分属不同作用域。new_positions内的a接住模块返回列表，再return给外层a；它们不必同名。形参privious虽然与调用者previous拼写不同，但位置传参仍有效，不以改名返工替代学习。

## 3. 模块和复用

教师模块d8_value_tools.py定义add_one(value)返回value+1。入口：

```python
import d8_value_tools
answer = d8_value_tools.add_one(4)
print(answer)
```

import不写.py；模块名.函数名表示调用该模块中已定义的函数。模块名使用合法下划线命名；入口脚本可有连字符，但不拿连字符文件名直接作import名字。

旧d8_alert_tools.py由教师准备high_locations和new_alert，学生只写模块入口和包装函数，不重抄旧算法。high_locations给当前达阈值区域；new_alert排除上次已报警者，保持当前遍历顺序。持续报警仍是报警，仅不属于本次新增提醒。当前达阈值且缺上次记录属于新增；等号达阈值。

已保存的d8-module-entry.py调用high_locations，west=30/阈值30输出['west']；d8-return-chain.py中的new_positions调用模块new_alert，输出['west']。教师等号/空/状态切换/输入不变测试证据见课堂日志和验证汇总，均不把复用旧函数算新独立实现。

## 4. 路径表示和实际定位

```python
from pathlib import Path
target = Path("reports") / "alert.csv"
print(Path.cwd())
print(target.name)
print(target.resolve())
```

Path构造路径对象；/连接路径段；.name取最后一段名称。Path.cwd()是本次运行的当前工作目录，不一定为工作区根或脚本目录。相对路径据cwd定位；resolve在本例返回绝对路径对象，不创建/读取文件，不要求目标存在。

若cwd是D:/study，target原表示reports/alert.csv，target.resolve()为D:/study/reports/alert.csv。

脚本所在目录这样取得：

```python
script_dir = Path(__file__).resolve().parent
target = script_dir / "reports" / "alert.csv"
```

__file__是当前脚本文件的路径，.parent取其所在文件夹；只在.py脚本语境演示。若脚本D:/study/code/review.py，则目标是D:/study/code/reports/alert.csv。只移动终端、不移动脚本，后一目标不变。

实际学生路径报告保留两种写法，教师从仓库根/03-code_codex运行：相对cwd方案改变，脚本目录方案不变。从03-code_codex启动两者相同，因为cwd与脚本目录恰好重合。该机制初次两次不懂后用目录树/PowerShell提示符补强；复盘两完整目标预测正确。

首稿未加引号alert.csv被解释为变量alert的csv属性，实际NameError。修为字符串'alert.csv'，打印文件名用target.name。用户保留单数alert.csv及单行打印，均不影响路径能力，不要求格式返工。

## 5. pdb调用栈与局部参数

调用链：入口→new_positions→new_alert→high_locations。调用栈记录尚未返回的调用，各层使用自己的局部参数名。被调用者的readings接收调用者current，两次读到同一温度字典。

学生实际在03-code_codex中完成：

```text
.\dbg d8-return-chain.py
> d8-return-chain.py(1)<module>()
-> import d8_alert_tools
(Pdb) b d8_alert_tools.py:4
Breakpoint 1 ... d8_alert_tools.py:4
(Pdb) c
> d8_alert_tools.py(4)high_locations()
-> sum = []
(Pdb) where
  d8-return-chain.py(9)<module>()
  -> a = new_positions(previous,current)
  d8-return-chain.py(4)new_positions()
  -> a = d8_alert_tools.new_alert(privious,current,30)
  d8_alert_tools.py(11)new_alert()
  -> group2 = high_locations(current,threshold)
> d8_alert_tools.py(4)high_locations()
  -> sum = []
(Pdb) p readings
{'east': 36, 'west': 30}
(Pdb) up
> d8_alert_tools.py(11)new_alert()
(Pdb) p current
{'east': 36, 'west': 30}
(Pdb) p readings
*** NameError: name 'readings' is not defined
(Pdb) down
> d8_alert_tools.py(4)high_locations()
(Pdb) p readings
{'east': 36, 'west': 30}
(Pdb) c
['west']
The program finished and will be restarted
> d8-return-chain.py(1)<module>()
-> import d8_alert_tools
(Pdb) q
```

栈中另有bdb.run/<string>等调试器层，本例略过。where的>标记当前选中观察层；up看上一层调用者，down看下一层被调用者。调用者/被调用者是相邻层相对关系。up/down不执行代码、不触发return，实际仍停high_locations第4行，sum=[]未执行；n/c会推动执行，停止条件不同。

查询readings的NameError仅是该调试表达式找不到名字，不表示目标程序运行崩溃。教师后续精确进程查询确认q后目标pdb进程不存在。全部记指导下操作完成，不冒充独立选断点/诊断。

## 6. 导入执行与直接运行保护

教师模块：

```python
print("MODULE LOADED")
def add_one(value):
    print("FUNCTION CALLED")
    return value + 1
```

入口仅import后print ENTRY READY，输出MODULE LOADED/ENTRY READY；入口再调用add_one(4)并打印返回，则增加FUNCTION CALLED/5。两预测学生正确、教师实际验证一致。顶层语句在导入时执行，def建立函数但不执行函数体。

Python自动给__name__赋值：本例模块直接运行时为'__main__'，被import时为模块名。普通if字符串比较形成常用保护：

```python
def add_one(value):
    return value + 1

if __name__ == "__main__":
    sample = 4
    answer = add_one(sample)
    print(answer)
```

函数定义在顶层供导入使用；只用于单独运行演示的样本、调用和打印进guard；import通常也在顶层，不能概括为所有非函数代码都进guard。

main是普通函数名，不会自动运行。def main中的print仅定义时不执行；顶层main()调用在导入时会执行；调用放guard才只在直接运行时执行。其他文件仍可显式模块.main()，guard不阻止调用。

学生入口d8-config-entry.py输出missing[]/changed['pump']/extra['fan']正确。工具模块早期写成'__main++'，导致直接运行也无输出；仅测导入安静无法发现此错。学生后来主动删除保护做打印实验，并明确不用教师再验证；最终源按原样保存，不能把有意删除当新错误或擅自改回。

## 7. 配置核查综合题

学生不采用旧报警依赖题，另要求全核心自写。教师曾将“不引入参数”机械解释为无形参，学生指出写死数据缺乏复用价值；现用check_config(expected,actual)，样本在外、参数传入，题面设计纠正不记学生失败。

核查missing=期望有实际无；extra=实际有期望无；changed=两边有但值不同。缺失/额外不混入changed；missing/changed按expected顺序，extra按actual顺序。函数不打印、不改输入，返回含三列表的字典。完整学生最终代码在学习册原件中，不重抄。

教师七例通过：标准、完全相同、实际空、期望空、双空、混合多项顺序、仅变化；三列表同次/跨次独立。两个遍历有不同职责；只遍历expected看不到actual额外键west，学生理由解释正确。循环次数分析后被学生明确取消，不能记算法已学。

植入错误把elif改独立if并去掉存在检查，遇north先加missing，再读取actual['north']会KeyError，比较未完成、不进changed。学生判断不能执行正确，根因初误，教师补讲；原正确函数的七例通过不因此抹去。

## 8. 复盘与复测边界

日复盘模块/返回链、两路径、guard/显式main输出预测正确；resolve用途另补讲；pdb执行/观察层经澄清后能解释；append返回值首答错、短对照后正确。已讲、提示完成、独立当日预测和约一周迁移分别记录。约11-09至11-13合并短变式，优先append/变量键/返回链/观察层，不要求重写旧函数。

公共工具go/dbg的Python支持由教师准备，Git/环境配置/测试批跑不计学生有效学习。日课实际时长看台账，不能把内容覆盖或教师工具成功当300分钟。
