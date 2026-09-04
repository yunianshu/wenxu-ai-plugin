# 验证

## 快速检查

无应用代码，无自动化单元/集成测试。本仓库级别的确定性校验以「文档完整性」为主：

```bash
py ai-project-steward/scripts/project_docs.py audit --root .
```

（检查 README / CHANGELOG / AGENTS / docs/ai 等基线文档存在性，以及 markdown 中引用的仓库路径是否真实存在。）

## 完整检查

无发布 / 全仓构建检查。托管插件自身的发布与验收流程遵循 `ai-project-steward/` 内部定义（见其 `ai-project-steward/skills/project-packager/` 等）。

## 手工或真实环境检查

- 文档人工审阅：确认 `README.md`、`AGENTS.md`、`docs/ai/` 内容与仓库实际状态一致。
- 未来新增插件时：在对应宿主环境（Codex / Zcode / Claude 等）中实际加载并验证清单与技能入口。
