# 开发指南

## 技术现状

仓库本身无应用代码、无构建链。`ai-project-steward/` 内为 Python 3 脚本与 Markdown skills；插件通过 `ai-project-steward/.codex-plugin/plugin.json`、`ai-project-steward/.zcode-plugin/plugin.json` 声明给宿主环境加载。

## 前置条件

- git：版本管理。
- Python 3：仅在运行 `ai-project-steward/` 内脚本时需要（如 `ai-project-steward/scripts/project_docs.py`、`ai-project-steward/scripts/diagram_docs.py`）。
- 本开发机备注：默认 `python`（`D:\soft\py`，3.13）存在无法加载标准库的环境问题，请用 `py` 启动器（3.14）。

## 构建与运行

当前没有可构建 / 可运行的应用，没有已验证的构建命令。仓库级确定性校验示例（文档完整性检查）：

```bash
py ai-project-steward/scripts/project_docs.py audit --root .
```

插件脚本的完整用法以 `ai-project-steward/` 内部各 skill 的 SKILL.md 为准。

## 环境与配置

无环境变量或运行配置文件要求。平台清单与版本见 `ai-project-steward/.codex-plugin/plugin.json`、`ai-project-steward/.zcode-plugin/plugin.json` 与 `ai-project-steward/CHANGELOG.md`。
