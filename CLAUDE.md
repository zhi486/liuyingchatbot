# chatbot

Ravenclaw: **RC-P2** | Ruflo Swarm: **hierarchical-mesh** (15 agents)

---

## Session Start (MUST do first)

1. `get_latest_context(project_id: "RC-P2")` — 加载上次 session 的上下文快照
2. `get_project(key: "RC-P2")` — 查看当前项目状态和任务树
3. `memory_search --query "[当前任务关键词]" --namespace patterns` — 搜索历史模式

如果 `get_latest_context` 返回了之前的 handoff/progress，继续其中标记的下一步工作。

## Session End (MUST do before ending)

1. `save_context(project_id: "RC-P2", content: "<进度摘要>", snapshot_type: "handoff")`
2. `end_work_session(session_id: "<id>", summary: "...", issues_worked: [...])`

---

## Multi-Agent Swarm

### When to Swarm
- **YES**: 3+ files, new features, cross-module refactoring, API changes, security, performance
- **NO**: single file edits, 1-2 line fixes, docs updates

### Agent Pipeline Pattern

Lead → architect → coder → tester → reviewer (SendMessage chain, no polling)

### Task Routing

| Task | Agents |
|------|--------|
| Bug Fix | researcher, coder, tester |
| Feature | architect, coder, tester, reviewer |
| Refactor | architect, coder, reviewer |
| Performance | perf-engineer, coder |
| Security | security-architect, auditor |

### MCP Tools

| Category | Key Tools |
|----------|-----------|
| Memory | `memory_store`, `memory_search`, `memory_search_unified` |
| Swarm | `swarm_init`, `swarm_status`, `swarm_health` |
| Agents | `agent_spawn`, `agent_list`, `agent_status` |

## Rules

- Do what has been asked; nothing more, nothing less
- ALWAYS read a file before editing it
- NEVER commit secrets, credentials, or .env files
- ALWAYS run tests after code changes
