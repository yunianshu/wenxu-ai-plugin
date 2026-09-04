# Development guide

## Detected technology

Python 3（标准库）、Markdown skills、git。

## Prerequisites

- Python 3.14（本机经 `py` 启动器或 `python3` 调用；裸 `python` 在本机损坏，勿用）。
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

钩子通过宿主注入的 CLAUDE_PLUGIN_ROOT 定位脚本路径；脚本不依赖环境变量之外的配置。
