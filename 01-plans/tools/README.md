# 教师学习册工具

`study_book.py`由助手维护和执行，不要求学生学习这些行政命令。学生新练习仍先在03-code_codex建立空白文件。

## 5分钟快速收尾

执行前读[唯一流程细则](../daily-close-rules.md#5分钟收尾2026-11-07)。常规日终预算300秒，课中增量准备，日终并行汇合：下一课差异预检、快照绑定的学习册校验/恢复与必要测试、有限网络探测。Git写操作由一个协调者执行，最终结果与阶段耗时写本机忽略回执。

既有功能验证仅在源/依赖/选项/用例哈希相同且最近通过时复用；本日原件、学习册与恢复字节仍完整核验。原件快照、最终提交的远程SHA/授权可见性确认，以及学习册/恢复验证同时通过，才清理显式日课清单。网络使用已验证路径优先、短超时、至多一次替代路径重试；预算到期保留本地恢复点并明确待同步，不能把5分钟目标当成功保证。

快速模式命令（计划JSON保存在本机，不上传凭据）：

```powershell
python .\01-plans\tools\daily_close.py --plan <本机JSON> --budget-seconds 300
```

计划字段以脚本`--help`和已验证配置为准。快速模式先推送原件快照，再生成/核验学习册，将拟删除项仅从Git索引移除，保留磁盘原件；最终提交推送核对通过后再逐文件清理。任一次上传失败，磁盘原件都仍在。`study_book.py`提供构建、校验和恢复；它的旧`clean`门槛仅兼容旧流程，不能替代快速模式的最终门槛。两者都是教师行政工具，不作为学生Git或工具作业。

### 计划JSON与并行检查

以下只是结构示例：假设`example.c`运行输出`OK`加换行。运行前须替换成当天真实日期、文件、预备导读、下一课材料及完整测试命令，所有输入在课中备妥。尤其将`classroom_ended_at`示例日期和16:00替换为本次采样的真实停表时刻，不复制示例时间作为成绩。

```json
{
  "date": "2026-11-08",
  "classroom_ended_at": "2026-11-08T16:00:00+08:00",
  "book": "02-logs/2026-11-08.md",
  "intro": "C:/Temp/close-intro.md",
  "visibility": "public",
  "manifest": [
    {"path": "02-logs/2026-11-08.md", "group": "原课堂记录", "role": "全文保全", "cleanup": false},
    {"path": "03-code_codex/example.c", "group": "学生代码", "role": "当日原作", "cleanup": true}
  ],
  "stage_paths": ["00-memory/MEMORY.md", "04-notes/lesson-2026-11-09.md", "04-notes/next-day-demo/d13/validation.json"],
  "required_paths": ["04-notes/lesson-2026-11-09.md", "04-notes/next-day-demo/d13/validation.json"],
  "checks": [{
    "name": "current-example",
    "commands": [
      ["gcc", "-std=c11", "-Wall", "-Wextra", "-Wpedantic", "-Werror", "{root}/03-code_codex/example.c", "-o", "{work}/current.exe"],
      ["{work}/current.exe"]
    ],
    "timeout_seconds": 40,
    "expected_stdout": "OK\n"
  }],
  "restore_checks": [{
    "name": "restored-example",
    "commands": [
      ["gcc", "-std=c11", "-Wall", "-Wextra", "-Wpedantic", "-Werror", "{restored}/03-code_codex/example.c", "-o", "{work}/restored.exe"],
      ["{work}/restored.exe"]
    ],
    "expected_stdout": "OK\n"
  }]
}
```

- 实际日终必须填写含时区ISO格式的`classroom_ended_at`。首跑`elapsed_seconds`含停表到命令启动的准备耗时和执行耗时，`execution_seconds`仅为命令执行，`clock_basis=classroom_stop`。未填时只有`command_start_only`基准，不能声称完成了端到端5分钟。
- `intro`可用本机绝对路径或工作区相对路径；清单、暂存与必备材料路径均为工作区相对路径。`visibility`按当前授权填写，不自动改仓库可见性。
- `manifest`列逐份保全原件；只有明确可清理的本日日课源标`cleanup: true`。原日志、公共工具、持续模块等保留。`group`、`role`为可选说明。
- `stage_paths`仅列需纳入本次提交的额外文件；清单路径、学习册和`.gitattributes`自动加入。`required_paths`仅检查材料已存在，不会自动把它们暂存，因此要上传的下一课材料也列入`stage_paths`。
- `checks`的各job相互并行；一个job内`commands`按顺序执行，`restore_checks`同理；`checks`工作目录是工作区根，`restore_checks`工作目录是离线恢复根。每个命令是argv数组，不经过shell；不要写管道或把整条shell命令塞成一个参数。各job使用独有临时输出文件名。
- `{root}`是工作区根，`{restored}`是按本日学习册精确恢复的离线根，`{work}`是临时构建目录。`timeout_seconds`缺省为40秒，受本次总截止时间约束；`stdin`只传给job最后一条命令，`expected_stdout`精确比较最后一条命令输出（包括换行）。
- 必须完整配置当日受影响功能、下一课最小例的`checks`，以及离线代表程序的`restore_checks`；多文件C程序还要列完整依赖。含`.c`或`.py`的清单必须至少配置一个恢复运行job，否则工具拒绝执行。空检查列表或只有无关命令不构成完整课程验收，工具只能验证你明确配置的任务，不能自动发现课程遗漏。已通过且哈希未变的课程证据，按唯一细则确定可复用范围。
- 工具会给清单原件添加`-text`并保真重暂存，首次提交前核对索引字节；不用为旧JSON的CRLF差异再补一轮上传。

### 失败、回执与续跑

`complete`退出码为0；`pending_sync`或`pending_validation`退出码为2。pending表示当前命令已结束且任务未完成，不表示有后台任务持续上传。若在网络/课程预检阶段失败，可能尚无本次Git提交，此时准确报告磁盘原件和hash/phase回执已保留；只有已实际产生的提交才称快照或待推提交。助手在后续交互中处理续跑，学生无需执行Git操作。

```powershell
python .\01-plans\tools\daily_close.py --plan <同一JSON> --budget-seconds 300 --resume
```

可用`--root <工作区路径>`指定工作区。主断点回执保存在`git rev-parse --git-path study-close/YYYY-MM-DD.json`所指文件；`00-memory/local-sync-state.json`仅可作为兼容摘要，不是快速模式的续跑来源；最后成功的网络路由保存在Git本机目录中的`study-close-route.json`，凭据不落盘，也不永久改Git代理配置。这些本机状态不打包进学习册。

`--resume`复用已产生的原snapshot/final commit，要求计划一致并核对输入哈希；哈希或远程状态变化时先审查、重新准备，不能假复用。续跑采用独立300秒attempt，`clock_basis=resume_attempt`，单列本次耗时，不抹去原先超时/失败。已完成日期不能再次普通启动；用`--resume`查看完成回执，不重新归档或清理。

## 手工日归档（兼容旧顺序）

新日终默认使用上面的快速模式。下列顺序仅供已有旧流程断点或基础工具调用；它在最终提交前清理，和快速模式的索引暂存/末尾清理不要混用。

1. 准备显式JSON清单：每项path、group、role、cleanup。仅日课独立源文件标cleanup=true；公共go、长期元数据、主项目、历史参考均false或不列入。
2. 原文件及学习记录先本地提交并推送，核对授权origin/main的SHA和可见性后生成学习册。归档清单路径使用Git -text属性保持原始字节，并在首次提交前检查索引字节，避免换行过滤造成补提交。
3. 准备学习册导读（重点、错点、实际证据、时间、明日入口），生成学习册：

```powershell
python .\01-plans\tools\study_book.py build --book 02-logs/YYYY-MM-DD.md --date YYYY-MM-DD --snapshot FULL_SHA --manifest MANIFEST.json --intro INTRO.md
python .\01-plans\tools\study_book.py verify --book 02-logs/YYYY-MM-DD.md
```

清单/导读可放系统临时目录；学习册嵌入完整原始字节、SHA-256、可阅读正文/代码和源路径，非仅链接。Markdown相对链接改指册内章节或正确的现行路径。已有日课日志作为原记录完整收录，学习册继续使用同一天日志路径。

4. 对清单原件完整恢复到新路径并逐份核验字节，运行代表性C/Python用例（已有同哈希功能回执按细则复用）。远程核对和本地验证支路汇合后再清理：

```powershell
python .\01-plans\tools\study_book.py clean --book 02-logs/YYYY-MM-DD.md
```

工具逐文件校验：学习册可读内容/恢复数据一致、Git快照原字节一致、当前源未变化、HEAD和授权远程main等于快照；任一前置不满足不开始清理。禁止目录递归删除、越界路径、符号链接、覆盖学生工作。执行中若并发变更立即停止后续清理，已经处理的源仍可从册恢复。

5. 更新现行入口，提交学习册/删除清单/下一课，再推送核对最终SHA。本机回执写忽略的local-sync-state.json，避免提交循环。网络失败按限时回退保留原件或已验证恢复点、写可续跑状态并明确待同步，不进行无预算的重试。

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
