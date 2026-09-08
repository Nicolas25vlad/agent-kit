# Execução econômica via agent-kit

CLI `agent` no PATH. **1 intenção = 1 comando.** JSON — leia `summary` primeiro.

## Config do projeto (`.agent-kit.toml`)

A IA escreve ao longo do uso; outros agentes leem automaticamente.

```bash
agent config learn              # detecta e salva commands.test, lint, etc.
agent config set commands.test "bun test"
agent config show
```

Comandos `test run`, `build run`, `deps install` usam config antes de detectar.

## Commit (mensagem obrigatória)

```bash
agent git suggest
agent git ship -m "feat(escopo): descrição"
agent land -m "feat: foo" --pr    # test + ship + ci status
```

## CI / PR

```bash
agent prep pr                     # PR + CI em 1 turno
agent ci status | agent ci logs
agent fix-ci                      # status + logs de falha
agent pr diff
agent git conflicts
```

## Setup

```bash
agent doctor
agent bootstrap                   # config learn + deps + compose + prep
```

## Env / Docker / FS

`agent env ingest` · `agent docker compose up -d` · `agent fs cd/grep/find`

Ver `prompts/env-handling.md` e `prompts/commit-message.md`.

## Regras

- `-m` obrigatório em ship/land — sem `--auto`
- **Nunca** `--human`
- Secrets: `.env.local` via `agent env`

## Economia e escopo

- Economize tokens sem sacrificar a qualidade final.
- Não use saudações ou conclusões genéricas.
- Não repita o pedido do usuário.
- Não escreva comentários óbvios no código.
- Não ofereça múltiplas alternativas; entregue a melhor solução.
- Para código, entregue diretamente, use nomes curtos e semânticos e evite linhas em branco excessivas.
- Para texto, use no máximo dois parágrafos e listas somente quando essenciais.
- Execute somente o que foi solicitado e encerre ao concluir.
- Não rode testes, builds, linters ou formatadores sem solicitação explícita.
- Não execute `git diff`, `git status` ou verificações finais não solicitadas.
- Não faça refactors ou melhorias fora do escopo.
- Não crie commits nem altere o Git sem solicitação explícita.
