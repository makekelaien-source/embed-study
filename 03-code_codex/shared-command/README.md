# 持续PC命令原型依赖（D12）

这些11份源/头是2026-11-08学生最终稿与教师读取适配的逐字节副本，保留供后续课程复用，不要求学生重抄。原稿、错误版本、教师测试和提示程度见02-logs/2026-11-08.md。分类/strict/console多为H2/H3后完成；bounded本题首稿通过；不要据可运行称全部独立掌握。

公共入口：d12-line-reader.h读取整行，d12-bounded-command.h检查/分类已有缓冲；main为d12-command-console.c。内部层需要时再展开，不要求同时记全。旧shared-text和week-review/review_input.c仍是持续依赖。

构建时加-I03-code_codex，再链接本目录六个.c（含console）与03-code_codex/shared-text两源、03-code_codex/week-review/review_input.c。不要将归档的错误稿或所有教师测试main一起编译。输入容量16、正文最多15，超长清理后继续。
