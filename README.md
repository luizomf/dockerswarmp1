# Docker Swarm Demo (Hostinger 3x VPS)

Cluster Docker Swarm com 3 VPS, Traefik na borda, API (FastAPI), frontend
(Nginx/SPA), PostgreSQL e deploy automatizado via webhook.

## Patrocínio (Hostinger)

Este projeto e o vídeo foram patrocinados pela Hostinger.

- Link: [hostinger.com/otaviomiranda](http://hostinger.com/otaviomiranda)
- Cupom: `OTAVIOMIRANDA`
- Benefício: `OTAVIOMIRANDA` dá **+10%** de desconto extra sobre o desconto do
  link.

## Comece Aqui

O guia canônico mostrado no vídeo está em:

- **[`docs/DEV_GUIDE.md`](docs/DEV_GUIDE.md)** (passo a passo completo, ordem
  oficial dos comandos)

## Arquitetura (Resumo)

- 3 nós Docker Swarm conectados por WireGuard.
- `kvm8` como edge node (Traefik 80/443) e nó fixo para Postgres.
- `kvm2` e `kvm4` como nós de carga para frontend/API.
- Overlay `public` para entrada via Traefik e overlay `internal` para tráfego
  interno.
- NFS sobre VPN para dados compartilhados.

## Quick Start Local (Compose)

Para rodar localmente, sem cluster:

```bash
git clone https://github.com/luizomf/dockerswarmp1.git
cd dockerswarmp1
cp .env.example .env
just upb
```

Acesse:

- Frontend: http://app.localhost
- API: http://app.localhost/api/visit

## Operação no Swarm

No manager de deploy:

```bash
set -a; source .env; set +a
just stack-deploy
just stack-logs api
just stack-logs traefik
docker stack ps dockerswarmp1
docker node ls
```

Licença: MIT.
