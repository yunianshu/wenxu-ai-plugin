# Development guide

## Detected technology

Python 3（标准库）、Markdown skills、git。

## Prerequisites

- Python 3；Windows 钩子使用 py -3 -X utf8，其他宿主使用 python3 -X utf8。解释器可用性以当前执行结果为准，不沿用历史环境故障推断。
- git。

## Build and run

无构建链。脚本直接以 CLI 运行，完整用法见各 SKILL.md。常用确定性校验：

```bash
py scripts/project_docs.py audit --root .        # 本目录文档集审计
py scripts/project_docs.py init --root . --subdir <plugin>   # 集合仓库为插件子目录建立文档集
py scripts/release_artifacts.py detect --root <repo>          # 发布产物探测
```

多宿主分发由上层集合仓库的统一同步工具完成（仓库根 tools/ 下的 sync-plugin.py，属仓库级而非本插件内容）。

## Environment and configuration

钩子在 Python 中读取宿主注入的 PLUGIN_ROOT 或 CLAUDE_PLUGIN_ROOT 来定位脚本，避免混用 cmd 的百分号变量与 PowerShell 语法。可选 PLUGIN_DATA / CLAUDE_PLUGIN_DATA 只用于提示去重，不写业务仓库。

更新 hook 定义后，Codex 可能要求在 /hooks 审阅并信任新定义；安装插件不代替宿主信任。不得手改 trusted_hash。重开会话用于确认新技能与钩子已加载。
