<p align="center">
  <img src="assets/logo.svg" alt="agent-kit" width="640">
</p>

<p align="center">Contexto, diagnósticos e operações repetíveis para agentes de código — em uma CLI Python stdlib-only.</p>

<p align="center">
  <a href="https://github.com/Nicolas25vlad/agent-kit/actions/workflows/ci.yml"><img src="https://github.com/Nicolas25vlad/agent-kit/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-22c55e" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/python-3.9%2B-3776AB" alt="Python 3.9+">
</p>

## O que resolve

`agent-kit` transforma tarefas recorrentes de agentes em comandos curtos que retornam JSON previsível: preparação de contexto, detecção do projeto, Git, CI, PRs, filesystem, ambiente e Docker.

Sem pip, sem runtime proprietário e sem dependências de terceiros: basta Python 3.9+.

## Instalação

### WSL, Linux e macOS

```bash
./install.sh
agent repo info
```

### Windows PowerShell

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
agent repo info
```

O instalador do Windows cria o wrapper em `%LOCALAPPDATA%\agent-kit\bin` e registra esse diretório no PATH do usuário. Abra um novo PowerShell após a instalação.

## Uso

```text
agent prep task              # contexto inicial em um turno
agent doctor                 # diagnóstico do ambiente
agent git snapshot           # estado Git compacto
agent test detect            # ferramentas de teste detectadas
agent build run --target lint
agent pr checks              # status da PR e checks
agent fs grep "TODO" src
agent repo info              # repositório e branch atuais
```

Todos os comandos são orientados a automação e escrevem JSON por padrão. Use `--human` quando precisar de uma saída legível no terminal.

## Arquitetura

```text
bin/agent                 launcher sem dependências
src/agent_kit/            comandos e operações
prompts/                  regras reutilizáveis para agentes
install.sh                instalador POSIX/WSL
install.ps1               instalador Windows
.github/workflows/ci.yml  verificação multi-Python
```

## Princípios

- stdlib-first e zero dependências de runtime;
- JSON estável para consumo por agentes;
- operações destrutivas explícitas;
- detecção antes de automação;
- segredos bloqueados antes de publicação;
- suporte nativo a Windows, WSL, Linux e macOS.

## Desenvolvimento

```bash
PYTHONPATH=src python -m agent_kit --help
python -m compileall -q src
```

O pipeline executa compilação e smoke tests em Python 3.9, 3.12 e 3.13 para pushes e pull requests contra `main`.

## Segurança

Não versione `.env`, tokens, credenciais ou saídas locais. O fluxo de publicação do CLI recusa arquivos com aparência sensível que não estejam ignorados.

Para reportar uma vulnerabilidade, abra uma issue sem incluir credenciais ou uma prova de conceito destrutiva.

## Licença

Distribuído sob a [MIT License](LICENSE).
