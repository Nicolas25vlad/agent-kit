# agent-kit — instruções para agentes

Use `agent` para todas as operações abaixo. JSON em stdout.

```
agent prep task              # início de tarefa
agent git snapshot|ship|sync|log|branch|add|stash
agent test detect|run
agent build run --target lint
agent deps install
agent pr list|review|open|merge|comment
agent fs ls|grep|read
agent repo info|find|clone
```

Ver `prompts/cursor-user-rule.md` para mapa completo.
