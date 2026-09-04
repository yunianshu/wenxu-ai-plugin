# Known issues

Record active limitations and durable workarounds. Remove entries when they are no longer true; use Git for history.

- 文档审计（project_docs.py audit）把反引号内带扩展名的 token 按仓库相对路径校验：描述性文件名（如在目标项目中生成的 start.bat）应写成普通文字，勿用路径式反引号。
- release_artifacts.py 的 audit 模式只检查 collect 输出布局（output-dir 根的 manifest.json），不校验 bundle 产物目录内的 manifest——两者语义不同，属既有行为。
- Windows 下裸 `python`（D:\soft\py，3.13）标准库加载损坏；一律用 `py` 或 `python3`（3.14）。
