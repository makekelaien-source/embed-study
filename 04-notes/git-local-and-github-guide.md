# 本地保存版本与同步GitHub操作指南

> 本项目根目录：D:/Apostgraduate/opencode/embed-study。2026-10-27已建立[私有GitHub仓库](https://github.com/makekelaien-source/embed-study)，main跟踪origin/main。最初仅两文件同步为历史，后获学生明确授权按[日终规则](../01-plans/daily-close-rules.md)保存学习代码、讲义、日志、记忆和计划等。当前最终结果以Git及本机00-memory/local-sync-state.json为准；[两文件首次回执](git-sync-status-2026-10-27.json)只供追溯。

## 一次性设置与当前范围

Git初始化、main分支及仓库局部署名已完成，不需要每天重做。署名Zhang_BoXuan，邮箱使用GitHub隐私邮箱；查询用git config --local --get-regexp '^user\.'。本地仓库管理目录是.git，不手动编辑或删除。

远程地址用git remote -v查看；只有尚无origin时才添加，已有时先核对，不盲目覆盖。本次采用GitHub CLI已登录连接，只在本仓库配置GitHub凭据助手，不把令牌写入文件或命令说明。

当前日终自动备份范围已扩展为日终规则列出的学习资料。本指南下方用原两个文件作命令示例；保存其他资料须选择相应路径，未add/commit的内容不会随push上传。工具私有配置与生成物按.gitignore排除，私有仓库并不自动备份任意本地文件。

## 每次保存到本地：查看→暂存→检查→提交

1. 保存编辑器里的文件，切到项目根目录并看状态：

```powershell
Set-Location 'D:\Apostgraduate\opencode\embed-study'
git status --short
```

??为未跟踪；右侧M（如“ M”）是工作区修改；左侧A/M表示已暂存的新文件/修改。同一个文件两边都可能有状态，表示暂存后又继续改了它。

2. 看这两个文件尚未暂存的差异：

```powershell
git --no-pager diff -- .gitignore 03-code/d8-python-first.py
```

-行是旧内容，+行是新内容。git diff默认比较工作区与暂存区；未跟踪文件通常不在这个diff中，要先阅读文件再选择暂存。

3. 选择本次保存的文件：

```powershell
git add -- .gitignore 03-code/d8-python-first.py
```

add不会产生版本，只更新暂存区。后续如果只改了一个文件，也可只add那个文件；暂存后再改文件，要再次add才能把最新修改放进去。

4. 检查将进入提交的确切内容：

```powershell
git --no-pager diff --cached
```

它比较暂存区与上次提交。确认只包含本次要保存的内容；空diff通常表示没有新的暂存改动，不必制造空提交。

5. 创建本地版本，说明换成本次真实改动：

```powershell
git commit -m "Describe this change"
git log -1 --oneline
git status --short -- .gitignore 03-code/d8-python-first.py
```

commit生成本地版本编号，不会自动上传。最后的状态若为空，只表示这两个指定文件没有未保存修改，不代表全部学习资料都已跟踪。

## 同步到GitHub

首次连接完成后，main跟踪origin/main。每次先完成本地提交，再执行：

```powershell
git push
```

首次建立跟踪关系使用：

```powershell
git push -u origin main
```

push只上传提交历史，不上传尚未commit的修改或未跟踪文件。改文件但没commit，单独push不会保存这些变化。

若从零创建本次私有远程，GitHub CLI可用以下一次性命令；当前仓库已创建后不要重复执行：

```powershell
gh repo create makekelaien-source/embed-study --private --source . --remote origin
```

凭据助手由本次连接流程配置。以后遇登录或权限错误先保留输出核对账号/仓库；推送被拒绝时检查远程新提交，不使用force覆盖远程。

## 判断是否真的同步成功

```powershell
git remote -v
git status --short --branch
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

本地HEAD与远程main编号相同，说明当前本地提交已同步；再检查GitHub仓库可见性是private，远程文件列表与本次选定学习资料一致。本机工具配置、生成物等不在同步范围；未跟踪文件仍不随push上传。

日常最短流程是：保存文件→git diff→git add选定文件→git diff --cached→git commit→git push。Git记录不能替代执行程序或测试，修改正确与保存成功分别验证。
