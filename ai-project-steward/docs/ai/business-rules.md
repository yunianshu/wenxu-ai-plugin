# Business rules

Record only current rules that cannot be reliably inferred from code. Each rule should identify its scope and affected module.

## Confirmed rules

- 发布版本永不发明：project-packager 从权威版本源（VERSION 或主构建清单）解析；多源冲突必须阻断并全部上报（release_artifacts.py）。
- scaffold 只补缺失、不覆盖已有脚本；模板含 TODO(project) 标记，发布前必须按真实项目细化（release_artifacts.py）。
- 打包产物必须是单一顶层目录的 tar.gz，目录名、归档名、内置 VERSION 与清单版本一致（release_artifacts.py）。
- 插件公共清单（.codex-plugin/.zcode-plugin）的变更必须评估对各宿主加载的影响；构建戳升号是分发更新机制的一部分（module-map 平台清单）。
- 本目录整体分发到各宿主：入库内容即分发内容，禁止密钥/缓存/本机私有路径（AGENTS.md Constraints）。
- doc_guard 是非强制的文档影响提醒：只运行只读 impact，不运行 sync/init，不创建业务仓库基线，也不根据固定结束语阻断任务。异常输入、Git 不可用与子进程超时返回 continue；有宿主 PLUGIN_DATA 时按会话和变更路径集合去重提醒。
- Skills 的流程服务用户授权范围：普通多文件修改不自动增加计划批准；文档、图表和打包按实际交付需要调用，不形成强制流水线。原生发布产物不必套服务部署包；真正的版本冲突只阻塞依赖定版的步骤。
