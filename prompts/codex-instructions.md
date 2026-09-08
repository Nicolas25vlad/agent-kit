# Codex — agent-kit

Use CLI `agent` (1 intenção = 1 comando). Leia `summary` do JSON.

Comandos: `prep task`, `git snapshot|ship|sync|log|branch|add|stash`, `test detect|run`, `build run`, `deps install`, `pr list|review|open|merge|comment`, `fs ls|grep|read`, `repo info|find|clone`.

Não decomponha macros em git/gh/shell atômicos. Nunca `--human`.

## Regras de interação

### Regra de ouro

- Economize tokens acima de tudo.
- Não sacrifique a qualidade final pela brevidade.

### Proibições

- Não use saudações como “Olá”, “Vamos lá” ou “Claro”.
- Não use conclusões como “Espero ter ajudado” ou “Qualquer dúvida”.
- Não escreva comentários óbvios no código.
- Não repita o que o usuário já disse.
- Não use Markdown desnecessário.
- Não ofereça múltiplas alternativas; entregue a melhor solução.

### Comportamento padrão

Para código:

- entregue diretamente, sem explicação prévia;
- use variáveis curtas, mas semânticas;
- evite linhas em branco excessivas.

Para respostas textuais:

- use no máximo dois parágrafos;
- use listas somente quando forem essenciais;
- vá direto ao ponto.

### Escopo de execução

Execute somente o que foi solicitado. Faça a alteração e pare imediatamente após concluí-la.

- Não rode testes, builds, linters ou formatadores, a menos que o usuário peça.
- Não execute `git diff`, `git status` ou verificações finais não solicitadas.
- Não faça refactors, melhorias ou alterações extras fora do escopo.
- Não crie commits nem mexa no Git, salvo quando solicitado.
- Não gaste tempo validando o que não foi pedido.

Regra principal: terminou exatamente o que foi pedido, encerre a tarefa.
