# Verification

## Fast checks

- 语法：`py -c "import ast; ast.parse(open('<script>',encoding='utf-8').read())"` 逐脚本。
- 文档：`py scripts/project_docs.py audit --root .`（0 issues 为过）。

## Full checks

- 上层仓库：`py tools/sync-plugin.py --check` 五宿主（ZCode/Claude/Codex/Kimi/agents）内容一致性全 PASS。
- project_docs.py 行为验证在沙箱集合仓库完成：--subdir init 落位、集合 audit 自动发现、impact 按子目录过滤、sync 自愈补齐、doc_guard JSON 形状兼容。

## Manual or real-environment checks

- 各宿主运行时是否加载新版本未逐一启动实测（文件级与注册表级已验证）；Claude/ZCode 需重启会话生效。
- scaffold 生成的部署脚本模板面向 POSIX/Linux 部署，本机仅做 bash -n 与 cmd 生命周期验证，未在真实生产环境执行。
