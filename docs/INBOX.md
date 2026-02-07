# Inbox (Ideias e Pendencias)

Objetivo: local de fácil acesso para pendências do projeto e novas
implementações. Tudo que vier aqui seguirá o mesmo fluxo descrito em `AGENTS.md`
(`PLAN.md`, `commit` e `CHANGELOG.md`). Este é o "backlog/inbox".

Regra do projeto:

- **Só implementamos** algo descrito aqui quando isso for promovido para
  `PLAN.md`.
- `PLAN.md` sempre descreve **apenas** o que esta sendo feito neste momento e
  deve ser limpo ao finalizar.

Como funciona?

- Escreva uma linha curta
- Opcional: contexto + objetivo + risco
- Se for algo sensível (segurança/infra), marque com `security`/`infra`

Regra para evitar conflito (o "um tocar no arquivo do outro"):

- Todo item deve ter um `Owner`.
- So o `Owner` mexe nos arquivos listados em `Files`.
- Contribuicao de quem nao e `Owner`:
  - sugestoes em comentario no item
  - ou rascunho em arquivo separado (ex: `docs/drafts/...`) e depois o `Owner`
    integra

Como usamos o Gemini:
- O Gemini nunca "toca" no repo. Ele so gera sugestoes (texto/snippets).
- Eu (Codex) faço a integracao e o commit.

Template recomendado:

```text
- [ ] <titulo curto> (tags: infra|app|video|docs|ci|security)
  Owner: user|codex|gemini
  Files:
  Contexto:
  Objetivo:
  Notas:
  Output:
```

## Novas (triagem)

- [ ]

## Prontas Para Virar PLAN (aprovadas)

- [ ]

## Estacionadas (depois do video)

- [ ]
