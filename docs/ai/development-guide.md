# 开发指南

## 技术现状

仓库本身无应用代码、无构建链。`ai-project-steward/` 内为 Python 3 脚本与 Markdown skills；插件通过 `ai-project-steward/.codex-plugin/plugin.json`、`ai-project-steward/.zcode-plugin/plugin.json` 声明给宿主环境加载。

## 前置条件

- git：版本管理。
- Python 3：仅在运行 `ai-project-steward/` 内脚本时需要（如 `ai-project-steward/scripts/project_docs.py`、`ai-project-steward/scripts/diagram_docs.py`）。
- 本开发机备注：默认 `python`（`D:\soft\py`，3.13）存在无法加载标准库的环境问题，请用 `py` 启动器（3.14）。

## 构建与运行

当前没有可构建 / 可运行的应用。仓库级确定性校验命令：

```bash
py ai-project-steward/scripts/project_docs.py audit --root .        # 根 + 已标记子目录文档集一并审计
py ai-project-steward/scripts/project_docs.py init --root . --subdir <plugin>   # 为插件子目录建立文档集
```

插件改动完成后，用统一同步工具把最新内容分发到本机各宿主并验证（ZCode / Claude Code 走插件市场+缓存+注册表全量更新，Codex / Kimi CLI / 共享 `~/.agents/skills` 走技能目录分发）：

```bash
py tools/sync-plugin.py --check   # 只读校验五宿主是否与仓库一致
py tools/sync-plugin.py           # 同步（内容变化时自动升 ZCode 构建戳与 Claude 版本号）并复验
py tools/sync-plugin.py --only claude,codex   # 仅指定宿主
```

同步工具会改写仓库内 `ai-project-steward/.codex-plugin/plugin.json` 的构建戳（内容有变化时），记得随插件改动一起提交。每次同步前各宿主的注册表/清单会自动备份到对应插件目录下的 backup-sync-宿主-时间戳 备份目录。

插件脚本的完整用法以 `ai-project-steward/` 内部各 skill 的 SKILL.md 为准。

## 环境与配置

无环境变量或运行配置文件要求。平台清单与版本见 `ai-project-steward/.codex-plugin/plugin.json`、`ai-project-steward/.zcode-plugin/plugin.json` 与 `ai-project-steward/CHANGELOG.md`。
