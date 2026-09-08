# Env vars — quando o user cola token no chat

## Fluxo obrigatório

Quando o usuário mandar credencial, token, API key ou `.env` no chat:

1. **Nunca** repetir o valor completo na resposta
2. **Nunca** commitar em git
3. Salvar com `agent env`:

```bash
# user mandou: ghp_xxxx... ou TOKEN=ghp_xxxx
agent env ingest "TOKEN=valor_colado"
# ou
agent env set GITHUB_TOKEN=valor_colado
```

4. Confirmar com `agent env list` (valores mascarados)
5. Rodar `agent env check` se existir `.env.example`

## Comandos

| Situação | Comando |
|----------|---------|
| User colou KEY=val ou bloco .env | `agent env ingest "<blob>"` |
| Set explícito | `agent env set KEY=valor` |
| Ver chaves (mascaradas) | `agent env list` |
| Faltando vs example | `agent env check` |

## Regras

- Preferir `.env.local` (nunca commitado) sobre `.env`
- Se user mandou só o token sem nome: perguntar a KEY ou inferir do contexto (`GITHUB_TOKEN`, `OPENAI_API_KEY`, etc.)
- Avisar se `.env.local` não está no `.gitignore`
- Output do `agent env` já mascara — não reimprimir secrets no chat

## Exemplo

User: "usa esse token ghp_abc123xyz"

```
agent env set GITHUB_TOKEN=ghp_abc123xyz
agent env list
```

Resposta ao user: "Token salvo em `.env.local` como `GITHUB_TOKEN` (mascarado)."
