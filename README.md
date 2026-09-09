<p align="center">
  <img src="assets/logo.svg" alt="agent-kit" width="640">
</p>

<p align="center"><strong>Contexto, diagnóstico e automação segura para agentes de código.</strong></p>

<p align="center">Uma CLI Python pequena, previsível e sem dependências de runtime.</p>

<p align="center">
  <a href="https://github.com/Nicolas25vlad/agent-kit/actions/workflows/ci.yml"><img src="https://github.com/Nicolas25vlad/agent-kit/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-22c55e" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/python-3.9%2B-3776AB" alt="Python 3.9+"><a href="https://github.com/Nicolas25vlad/agent-kit/stargazers"><img src="https://img.shields.io/github/stars/Nicolas25vlad/agent-kit?style=flat" alt="GitHub stars"></a>
</p>

## Instalação rápida

Instala ou atualiza o checkout local do `agent-kit` e registra o comando `agent` no PATH:

```bash
curl -fsSL https://raw.githubusercontent.com/Nicolas25vlad/agent-kit/main/install.sh | bash -s -- --remote
```

O repositório fica em `~/.local/share/agent-kit`. Execute novamente o mesmo comando para atualizar. Funciona em WSL, Linux, macOS e Git Bash; requer Git, Python 3.9+ e `curl`.

## Índice

- [Visão geral](#visão-geral)
- [Por que existe](#por-que-existe)
- [Instalação](#instalação)
- [Primeiros passos](#primeiros-passos)
- [Comandos](#comandos)
- [Saída JSON](#saída-json)
- [Configuração](#configuração)
- [Arquitetura](#arquitetura)
- [Segurança](#segurança)
- [Desenvolvimento](#desenvolvimento)
- [Contribuição](#contribuição)
- [Licença](#licença)

## Visão geral

`agent-kit` é uma CLI para reduzir o trabalho repetitivo de agentes de código. Ela reúne em uma interface única as operações que normalmente exigem vários comandos, ferramentas e formatos de saída:

- carregar contexto de um projeto;
- detectar linguagens, ferramentas e arquivos relevantes;
- consultar ou alterar o estado do Git;
- preparar commits, PRs e diagnósticos de CI;
- pesquisar e ler arquivos com limites seguros;
- verificar ambiente, variáveis e Docker.

O resultado padrão é JSON compacto, pensado para ser lido por agentes, scripts e pipelines. A opção `--human` troca a saída para uma forma mais confortável no terminal.

## Por que existe

Agentes perdem contexto quando cada projeto usa uma sequência diferente de comandos. `agent-kit` cria uma camada operacional simples, local e portátil, sem esconder o Git nem exigir uma plataforma própria.

### Princípios

| Princípio | Decisão |
| --- | --- |
| Portabilidade | Python 3.9+ em Windows, WSL, Linux e macOS |
| Dependências | somente biblioteca padrão no runtime |
| Automação | JSON estável e comandos compostos |
| Segurança | operações destrutivas explícitas e bloqueio de arquivos sensíveis |
| Transparência | Git, GitHub CLI, Docker e ferramentas locais continuam visíveis |
| Manutenção | módulos pequenos por domínio, sem framework próprio |

## Instalação

### WSL, Linux e macOS

```bash
git clone https://github.com/Nicolas25vlad/agent-kit.git
cd agent-kit
./install.sh
agent repo info
```

O instalador cria um wrapper em `~/.local/bin/agent`, aponta para o checkout atual e adiciona o diretório ao `.bashrc` ou `.zshrc` quando necessário. Não instala pacotes via pip.

### Windows PowerShell

```powershell
git clone https://github.com/Nicolas25vlad/agent-kit.git
Set-Location agent-kit
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
agent repo info
```

O instalador cria `%LOCALAPPDATA%\agent-kit\bin\agent.cmd`, registra o diretório no PATH do usuário e usa `py -3` ou `python`. Abra um novo PowerShell quando o instalador terminar.

### Requisitos

- Python 3.9 ou superior;
- Git para comandos de repositório;
- `gh` autenticado para operações GitHub;
- Docker apenas para os comandos do domínio `docker`;
- WSL apenas para instalação e execução no ambiente Linux do Windows.

## Primeiros passos

```bash
# entender o projeto atual
agent prep task

# diagnosticar o ambiente
agent doctor

# ver o estado do repositório
agent git snapshot

# descobrir ferramentas de teste disponíveis
agent test detect

# saída legível para humanos
agent --human prep task
```

Um fluxo típico de agente fica assim:

```text
prep → detect → inspect → change → test/build → git snapshot → PR/CI
```

O CLI não substitui a revisão humana. Ele organiza o contexto e reduz comandos acidentais.

## Comandos

### Contexto e diagnóstico

| Comando | Uso |
| --- | --- |
| `agent prep task` | contexto inicial do projeto em um turno |
| `agent prep task --pr` | contexto com PR atual, quando existir |
| `agent prep pr` | resumo da PR e dos últimos checks |
| `agent doctor` | diagnóstico geral do ambiente |
| `agent test detect` | ferramentas e comandos de teste detectados |
| `agent env list` | variáveis de ambiente disponíveis conforme configuração |
| `agent env check` | verifica configuração de ambiente |

### Git e publicação

| Comando | Uso |
| --- | --- |
| `agent git snapshot` | branch, tracking, alterações e último commit |
| `agent git suggest` | sugere uma mensagem de commit |
| `agent git add [paths]` | adiciona arquivos específicos |
| `agent git ship -m "mensagem"` | stage, commit e push controlados |
| `agent git ship -m "..." --pr` | publica e abre uma PR |
| `agent git sync --rebase` | fetch, pull e push sincronizados |
| `agent git log` | histórico compacto |
| `agent git diff --stat` | resumo da diferença |
| `agent git diff --cached` | diferença staged |
| `agent git diff --check` | verifica whitespace problemático |
| `agent git branch` | branch atual e branches locais |
| `agent git remote` | lista remotes |
| `agent git config user.name` | consulta configuração Git |
| `agent git tag` | lista tags |
| `agent git check-ignore arquivo` | verifica se um caminho é ignorado |
| `agent git stash push -m "..."` | guarda alterações temporariamente |
| `agent git conflicts` | localiza conflitos e marcadores |

### GitHub e CI

| Comando | Uso |
| --- | --- |
| `agent pr list` | lista PRs abertas |
| `agent pr open -t "Título"` | abre uma PR |
| `agent pr review -n 12` | consulta a revisão |
| `agent pr checks -n 12` | consulta checks da PR |
| `agent pr comment -n 12 -b "..."` | comenta na PR |
| `agent pr merge -n 12` | solicita merge pela estratégia escolhida |
| `agent ci status` | status dos workflows recentes |
| `agent ci logs -n RUN_ID` | logs de um workflow |
| `agent ci view -n RUN_ID` | resumo de um workflow |
| `agent ci watch -n RUN_ID` | acompanha até terminar |
| `agent ci workflows` | lista workflows |
| `agent ci run workflow.yml --ref main` | dispara um workflow |

### GitHub e releases

| Comando | Uso |
| --- | --- |
| `agent github auth` | consulta autenticação do GitHub CLI |
| `agent github api repos/OWNER/REPO` | consulta a API do GitHub |
| `agent github api repos/OWNER/REPO --method PUT --input body.json` | envia payload JSON para a API |
| `agent github release list` | lista releases |
| `agent github release view --tag v1.0.0` | consulta uma release |
| `agent github release create --tag v1.0.0` | cria uma release com notas automáticas |

### Arquivos, projeto e execução

| Comando | Uso |
| --- | --- |
| `agent fs ls` | lista arquivos com limites |
| `agent fs grep "padrão" src` | pesquisa conteúdo |
| `agent fs find "nome"` | localiza arquivos |
| `agent fs read README.md` | lê um arquivo em fatias |
| `agent repo info` | identifica repo, branch e origem |
| `agent repo find nome` | encontra repositórios locais |
| `agent repo clone URL` | clona um repositório |
| `agent build run --target lint` | executa o alvo detectado |
| `agent build run --target test` | executa testes detectados |
| `agent deps install` | instala dependências detectadas |
| `agent docker compose ps` | consulta serviços Docker |

Veja todas as opções com:

```bash
agent --help
agent <domínio> --help
```

Para um binário externo ainda não mapeado, use `agent exec`. Ele não abre um shell intermediário e sempre retorna JSON:

```bash
agent exec git status --short
agent exec gh run view 12345
agent exec wsl.exe bash -lc "agent repo info"
agent exec python --version
```

## Saída JSON

Por padrão, cada operação retorna um objeto com campos previsíveis:

```json
{
  "ok": true,
  "command": "repo.info",
  "summary": "agent-kit (main)",
  "data": {
    "name": "agent-kit",
    "branch": "main"
  }
}
```

Erros também seguem o mesmo contrato, com `ok: false` e um objeto `error` contendo código e mensagem. Isso permite que um agente decida o próximo passo sem fazer parsing de texto humano.

## Configuração

Quando existe `.agent-kit.toml`, o projeto pode declarar caminhos ignorados, arquivo de ambiente e integração Docker:

```toml
[paths]
skip = ["node_modules", ".git", "dist", "build"]

[env]
file = ".env.local"

[docker]
compose = true
```

Comandos relacionados:

```bash
agent config show
agent config learn
agent config set commands.test "python -m pytest"
agent env set API_URL=https://example.test --file .env.local
```

Arquivos `.env`, tokens, caches e ambientes virtuais permanecem fora do versionamento por padrão.

## Arquitetura

```text
agent-kit/
├── bin/agent                 launcher POSIX/WSL
├── src/agent_kit/
│   ├── __main__.py           parser e roteamento da CLI
│   ├── prep_ops.py           contexto inicial
│   ├── git_ops.py            Git e publicação
│   ├── pr_ops.py             GitHub CLI e PRs
│   ├── ci_ops.py             workflows e logs
│   ├── fs_ops.py             leitura e busca de arquivos
│   ├── detect.py             detecção de ferramentas
│   └── *_ops.py              domínios Docker, ambiente e build
├── prompts/                  regras reutilizáveis para agentes
├── install.sh                instalador POSIX/WSL
├── install.ps1               instalador Windows
├── assets/logo.svg           identidade visual
└── .github/workflows/ci.yml  CI multi-Python
```

Cada domínio chama ferramentas locais com argumentos explícitos e converte o resultado para o contrato JSON comum. O projeto não mantém daemon, banco de dados ou serviço remoto.

## Segurança

- não inclua segredos em issues, PRs, logs ou commits;
- não versione `.env`, tokens, credenciais ou dumps locais;
- revise `agent git snapshot` antes de publicar;
- o fluxo de publicação bloqueia arquivos com aparência sensível que não estejam ignorados;
- comandos destrutivos, como descarte de alterações e remoção de volumes, exigem subcomandos explícitos;
- autenticação GitHub continua sob controle do `gh` instalado na máquina.

Para reportar uma vulnerabilidade, abra uma issue sem credenciais nem uma prova de conceito destrutiva. Para um relato sensível, contate o mantenedor antes de publicar detalhes.

## CI e proteção da `main`

O GitHub Actions executa, em cada push ou pull request para `main`:

1. compilação dos módulos Python;
2. smoke test de `--version`;
3. smoke test de `--help`;
4. matriz Python 3.9, 3.12 e 3.13.

A branch `main` exige pull request, uma aprovação, todos os checks obrigatórios, histórico linear e resolução das conversas. Force-push e exclusão da branch estão desativados.

## Desenvolvimento

```bash
git clone https://github.com/Nicolas25vlad/agent-kit.git
cd agent-kit
PYTHONPATH=src python -m agent_kit --help
python -m compileall -q src
```

O projeto não precisa de `pip install` para funcionar. O CI é a fonte de validação multi-versão; ferramentas adicionais são detectadas pelo próprio CLI quando usadas.

## Contribuição

1. crie uma branch curta a partir de `main`;
2. mantenha a mudança focada no domínio afetado;
3. preserve o contrato JSON;
4. atualize o README quando o comando público mudar;
5. abra uma pull request descrevendo comportamento e impacto.

Commits seguem Conventional Commits, por exemplo:

```text
feat: add repository context command
fix: block unsafe publication path
docs: expand command reference
```

## Licença

Distribuído sob a [MIT License](LICENSE).
