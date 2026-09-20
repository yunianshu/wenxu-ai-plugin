# 验证

## 最小相关检查

```powershell
python3 -X utf8 -B -m unittest discover -s "ai-project-steward/tests" -v
python3 -X utf8 "ai-project-steward/scripts/project_docs.py" audit --root .
```

钩子测试使用真实临时 Git 仓库和等价宿主 payload；覆盖异常输入、中文空格路径、只读性、非阻断输出、去重及子进程错误。worktree 测试在真实 Git 仓库上走 create→commit→merge→remove 全流程，断言已合并分支的空间目录被删除、变空父目录被清理、`--delete-branch` 连分支引用一起删除、脏工作区与未合并分支被拒绝且默认分支引用保留。Windows 下还执行清单中的 PowerShell、pwsh 和 cmd 启动命令。

## 分发校验

```powershell
python3 -X utf8 "tools/sync-plugin.py" --check --only codex
```

Codex 检查完整插件源、安装版本与对应缓存，而非仅检查 Skills。其他宿主使用 --only 单独指定，未运行的检查不得标记通过。

## 验证边界

Python 测试与缓存一致不等于已完成宿主交互测试。定义变化后应在新会话确认钩子加载；新信任审批需用户在宿主中完成，自动化不能写入 trusted_hash 代替。

文档审计是结构与引用检查，不要求为了通过审计扩展普通任务范围。服务部署脚本仅在相关发布任务中验证，本次钩子/指令修改不要求构建无关应用或在生产环境演练恢复。
