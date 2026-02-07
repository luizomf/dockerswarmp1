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

- [ ] Subir o swarm (tags: infra)
  Owner: user
  Files: N/A (VPS)
  Contexto: Podemos subir o swarm (swarm init).
  Objetivo: Iniciar o cluster.
  Notas: Isso foi um teste de nota (vamos fazer isso mesmo).
  Output: docs/REBUILD_MANUAL.md + comandos validados

- [ ] Redes da stack parecem incorretas (tags: infra)
  Owner: codex
  Files: docker/stack.yaml
  Contexto: Traefik está em `public`, mas deveria estar em `public` + `internal`.
  Objetivo: Confirmar e corrigir redes/labels/entrypoints.
  Notas: Verificar antes no cluster (o que e edge/internal de verdade).
  Output: commit + changelog

- [ ] HTML do Frontend (tags: video)
  Owner: gemini
  Files: frontend/index.html frontend/style.css
  Contexto: O frontend esta bonito, mas nao fala nada do link/cupom.
  Objetivo: Incluir link e cupom (Hostinger) visivel e bonito pra aparecer no video.
  Notas: Gemini gera 2-3 variacoes de copy/layout; Codex integra.
  Output: 1 commit com a pagina atualizada

## Prontas Para Virar PLAN (aprovadas)

- [ ]

## Estacionadas (depois do video)

- [ ]
