# Business rules

Record only current rules that cannot be reliably inferred from code. Each rule should identify its scope and affected module.

## Confirmed rules

- 发布版本永不发明：project-packager 从权威版本源（VERSION 或主构建清单）解析；多源冲突必须阻断并全部上报（release_artifacts.py）。
- scaffold 只补缺失、不覆盖已有脚本；模板含 TODO(project) 标记，发布前必须按真实项目细化（release_artifacts.py）。
- 打包产物必须是单一顶层目录的 tar.gz，目录名、归档名、内置 VERSION 与清单版本一致（release_artifacts.py）。
- 插件公共清单（.codex-plugin/.zcode-plugin）的变更必须评估对各宿主加载的影响；构建戳升号是分发更新机制的一部分（module-map 平台清单）。
- 本目录整体分发到各宿主：入库内容即分发内容，禁止密钥/缓存/本机私有路径（AGENTS.md Constraints）。
- doc_guard 钩子以『无需更新文档』等确认词放行；钩子对宿主下发的字面 null/非对象 payload 放行不崩溃（doc_guard.py）。
