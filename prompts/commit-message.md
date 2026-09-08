# Mensagem de commit — obrigatória

## Regra

`agent git ship` e `agent git commit` **exigem `-m`**. A IA deve escrever a mensagem explicitamente — não existe `--auto`.

## Fluxo

```bash
agent git snapshot                    # opcional: ver o que mudou
agent git suggest                     # rascunho heurístico (só referência)
agent git ship -m "feat(escopo): descrição clara"
```

## Formato

Conventional Commits em PT-BR:

```
tipo(escopo): descrição no imperativo
```

Tipos: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

## O que `suggest` faz

Retorna `data.draft` — **rascunho**, não commita. A IA deve:
1. Ler o diff em `data`
2. Revisar/corrigir o rascunho
3. Escrever `-m` com mensagem própria

## Proibido

- `agent git ship` sem `-m`
- Usar `data.draft` sem revisar
- Mensagens genéricas: "update", "fix", "changes", "wip"
