# Claude Code — agent-kit

Macro CLI `agent`. JSON → `summary` primeiro.

Início de tarefa: `agent prep task --pr`  
Git: `agent git snapshot`, `agent git ship -m "..." --pr --with-tests`  
Testes: `agent test detect`, `agent test run`  
FS: `agent fs grep`, `agent fs read`  
PR: `agent pr review`, `agent pr comment -b "..."`

Proibido: status+diff+log separados quando existe comando `agent`.
