# Known issues

Record active limitations and durable workarounds. Remove entries when they are no longer true; use Git for history.

- 文档审计（project_docs.py audit）把反引号内带扩展名的 token 按仓库相对路径校验：描述性文件名（如在目标项目中生成的 start.bat）应写成普通文字，勿用路径式反引号。
- release_artifacts.py 的 audit 模式只检查 collect 输出布局（output-dir 根的 manifest.json），不校验 bundle 产物目录内的 manifest——两者语义不同，属既有行为。
- 历史 Windows 命令使用 cmd 风格环境变量，不能在 PowerShell 中可靠展开；当前 hooks.json 已改为在 Python 内解析环境变量。解释器故障需要按当前运行证据判断。
- Stop 提醒只知道工作区差异，无法准确归属到本轮任务，也不证明文档一定有误；因此只提示、不阻断。只读审查遇到既有改动时无需为提示修改文件。
