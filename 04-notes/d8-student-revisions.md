# D8错误稿与实验版本（来源分清）

> 以下为聊天/教师当时读取的版本转录，非最终源原字节备份。最终学生源另按原字节收入学习册。这里的错误不得冒充最终正确实现；有意实验不得标成失误。

## 路径首稿：字符串未加引号（学生聊天和实际源一致）

```python
from pathlib import Path
target = Path("reports") / alert.csv
print(Path.cwd(),alert.csv,target.resolve())
```

教师实际运行第2行NameError: name 'alert' is not defined。修订是学生自己将文件名写为字符串，并用target.name打印。后续保留单数alert.csv，不以题面alerts.csv之s差异反复返工。

## 路径过渡稿（学生提交）

```python
from pathlib import Path
target = Path("reports") / "alert.csv"
print(Path.cwd(),target.name,target.resolve())
```

双目录运行目标随cwd改变，随后学生自己加入脚本目录对照。最终完整源见d8-path-report.py。

## guard早期实际读取版本：条件尾部加号

旧check_config函数体原样保留；当时文件末尾为：

```python
expected = {"east": 30, "west": 28, "north": 32}
actual = {"east": 30, "west": 35, "roof": 25}
if __name__ == "__main++":
    dicktionary = check_config(expected,actual)
    for item in dicktionary :
        print(dicktionary[item])
```

教师运行入口输出正确，但直接运行工具模块无输出，定位字符串未匹配'__main__'。这说明导入静默不足以证明guard两个分支都对；并非异常报错。

## 最终主动实验：删除guard（学生明确说明）

学生主动删除guard来验证顶层打印，明确不用教师再验证。最终d8_config_tools.py保留函数及顶层样本/调用/打印，是有意实验，不标作遗忘保护；不代改、不补填未贴出的实验输出。

## 口头预测的原始错误与反馈

- 嵌套read_temperature/report打印返回题：首答east:18/east，实际18/None，H2补讲。
- data={'east':18,'name':99}、name='east'时，data[name]/data['name']首答99/KeyError，实际18/99；学生后续自述没仔细看题，记录自述但不据此改写首答。
- append复盘首答fan/"changed":fan，实际['fan']/None；短对照直接取列表后回答['fan']正确。
- 独立if缺键植错：不能运行判断对，原因初述比较item/都加changed，实际访问actual['north']先KeyError，未追加north到changed；教师补讲。
- pdb复盘“返回up到调用层”含混；两位置表澄清后明确只是切观察、n/c才推动执行。

没有学生作答的旧静音报告空文件不记失败。教师无参数硬编码题面问题不归为学生能力缺陷。全部提示/学生实际回执详见原课堂记录。
