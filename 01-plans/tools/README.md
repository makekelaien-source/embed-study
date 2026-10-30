# 教师学习册工具

`study_book.py`由助手维护和执行，不要求学生学习这些行政命令。学生新练习仍先在03-code_codex建立空白文件。

## 日归档

1. 准备显式JSON清单：每项path、group、role、cleanup。仅日课独立源文件标cleanup=true；公共go、长期元数据、主项目、历史参考均false或不列入。
2. 原文件及学习记录先提交，推送授权origin/main并核对SHA。归档清单路径使用Git -text属性保持原始字节，避免换行过滤破坏恢复校验。
3. 准备学习册导读（重点、错点、实际证据、时间、明日入口），生成学习册：

```powershell
python .\01-plans\tools\study_book.py build --book 02-logs/YYYY-MM-DD.md --date YYYY-MM-DD --snapshot FULL_SHA --manifest MANIFEST.json --intro INTRO.md
python .\01-plans\tools\study_book.py verify --book 02-logs/YYYY-MM-DD.md
```

清单/导读可放系统临时目录；学习册嵌入完整原始字节、SHA-256、可阅读正文/代码和源路径，非仅链接。Markdown相对链接改指册内章节或正确的现行路径。已有日课日志作为原记录完整收录，学习册继续使用同一天日志路径。

4. 抽样恢复C/Python到临时新路径并核验字节，运行代表性用例；再清理：

```powershell
python .\01-plans\tools\study_book.py clean --book 02-logs/YYYY-MM-DD.md
```

工具逐文件校验：学习册可读内容/恢复数据一致、Git快照原字节一致、当前源未变化、HEAD和授权远程main等于快照；任一前置不满足不开始清理。禁止目录递归删除、越界路径、符号链接、覆盖学生工作。执行中若并发变更立即停止后续清理，已经处理的源仍可从册恢复。

5. 更新现行入口，提交学习册/删除清单/下一课，再推送核对最终SHA。本机回执写忽略的local-sync-state.json，避免提交循环。网络失败保留原件或已验证恢复点，明确报告。

## 恢复单文件

```powershell
python .\01-plans\tools\study_book.py restore --book 02-logs/YYYY-MM-DD.md --source 03-code_codex/NAME.c
```

无需网络即可从学习册按原字节恢复。目标存在时拒绝覆盖；可用--output指定另一个工作区内的新路径。教师批测优先用系统临时副本，避免把临时测试文件重新当成学生练习。

## 工具验证

```powershell
python -m unittest discover -s 01-plans/tools/tests -v
```

覆盖恢复保真、嵌套代码围栏、源码并发改动、未推送快照、正文篡改、路径边界和公共工具保留；测试仅使用系统临时Git仓库及本地bare远程。

公开仓库（学生2026-10-30授权）：清理明确传--visibility public；默认仍校验private。两种情况都验证远程SHA、完整学习册、原件字节与边界。工具10项测试已通过。
