# 开发指南

仓库托管 Python 标准库脚本、Markdown Skills 与宿主插件清单。无应用构建链。先读相关 AGENTS 与实际脚本，工具命令以 --help 和本次验证为准。

## 开发与验证

- Python 3 与 Git；Windows 可用 py -3，跨平台可用 python3。启动钩子显式选择 UTF-8，不按历史记录假定某个解释器仍损坏。
- 在仓库根运行 python3 -X utf8 -B -m unittest discover -s ai-project-steward/tests -v，验证钩子行为。
- 文档检查：python3 -X utf8 ai-project-steward/scripts/project_docs.py audit --root .；这是路径/结构检查，不代替语义审查。

## 本地分发

仓库工具 tools/sync-plugin.py 支持 --only 指定宿主、--check 只读校验。更新已安装 Codex 插件使用：

```powershell
python3 -X utf8 "tools/sync-plugin.py" --only codex
python3 -X utf8 "tools/sync-plugin.py" --check --only codex
```

Codex 分发从 CLI 获取 ai-project-steward@personal 的实际本地源路径，复制完整插件后通过 codex plugin add 更新缓存，核对源、安装版本与缓存内容。同一已安装版本内容变化时调用官方 plugin-creator 缓存戳 helper。不要仅复制 Skills 后声称钩子已更新。

本工具不手改 Codex 市场或 trusted_hash。钩子定义变化后，宿主可能要求 /hooks 审阅并信任；重新打开会话验证实际加载。同步本身不授权 Git 提交/推送。

ZCode / Claude 使用各自既有市场、缓存和注册表分发；Kimi / agents 复制 Skills。未指定 --only 会尝试全部宿主，仅在确实要求跨宿主同步时使用。复制保留额外文件并由校验报告，不递归删除安装目标。

## Skills 来源

本地 loose Skills 与插件内同名 Skills 可能同时被发现。在 Codex 中可使用 skills.config 按具体 SKILL.md 路径禁用重复拷贝，保留插件能力；不必删除其他宿主使用的文件。改动后复核有效目录，不对官方缓存做手工覆盖。

插件源码内不得包含本机备份、密钥或运行时缓存。变更以源码为准，经分发进入宿主；项目文档与插件文档分别维护其所属范围。
