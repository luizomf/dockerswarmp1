# dockerswarmp1

Projeto de demonstração para um cluster Docker Swarm com 3 VPS (Hostinger),
Traefik como edge, API em FastAPI, frontend estático via Nginx e PostgreSQL 18.
As imagens são buildadas no GitHub Actions e publicadas no GHCR, e o deploy é
feito via webhook.

## Visão geral

- 3 nós Swarm (todos managers): kvm2, kvm4, kvm8.
- `kvm8` é o edge público (Traefik + Postgres fixos nele).
- Frontend e API ficam no mesmo domínio (`APP_DOMAIN`).
- API responde em `/api`.
- Webhook do GitHub aciona deploy via watcher + NFS.

## Domínios e nós (do vídeo)

| Node | Public IP | WireGuard IP | Domain |
| --- | --- | --- | --- |
| kvm2 | 76.13.71.178 | 10.100.0.2 | inprod.cloud |
| kvm4 | 191.101.70.130 | 10.100.0.4 | otaviomiranda.cloud |
| kvm8 | 89.116.73.152 | 10.100.0.8 | myswarm.cloud |

Notas:

- Só o `kvm8` fica exposto na internet (Traefik na borda).
- `APP_DOMAIN` apontado para `kvm8` (ex: `app.myswarm.cloud`).
- `kvm2` e `kvm4` ficam fechados no firewall, acessados apenas via WireGuard.

## Pré-requisitos

- Docker Engine + plugin de Compose.
- `just` instalado.
- WireGuard configurado (rede `10.100.0.0/24`).
- UFW ativo e regras de Swarm liberadas na rede WireGuard.
- NFS server: `nfs-kernel-server` no `kvm8`.
- NFS clients: `nfs-common` nos demais nós.

## Variáveis de ambiente

Copie `.env.example` para `.env` nos managers (principalmente no `kvm8`):

```bash
cp .env.example .env
```

As variáveis essenciais para o Swarm:

- `APP_DOMAIN`
- `EMAIL`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `GITHUB_WEBHOOK_SECRET`
- `VISIT_SALT` (opcional)

O `just` carrega `.env` automaticamente (`set dotenv-load := true`).

## CI / GHCR

Este repositório possui um workflow que builda e envia imagens para o GHCR.
Para o webhook funcionar, configure no GitHub:

- `DEPLOY_WEBHOOK_URL` (ex: `https://app.myswarm.cloud/api/webhook/github`)
- `DEPLOY_WEBHOOK_SECRET` (o mesmo valor de `GITHUB_WEBHOOK_SECRET` do servidor)

Para o Swarm fazer pull das imagens privadas do GHCR, faça login no registry
no `kvm8` (ou em todos os nós):

```bash
docker login ghcr.io -u <seu-usuario> -p <seu-PAT>
```

O token precisa ao menos de `read:packages`.

## WireGuard (resumo)

Esta repo assume que os nós se enxergam por WireGuard em `10.100.0.0/24`.
Garanta conectividade entre todos os nós antes do Swarm.

## Firewall / UFW

Exemplo do mínimo necessário (ajuste para o seu ambiente):

```bash
ufw default deny incoming
ufw default allow outgoing

# SSH apenas do seu IP
ufw allow from <SEU_IP>/32 to any port 22 proto tcp

# Swarm na rede WireGuard
ufw allow in on wg0 from 10.100.0.0/24 to any port 2377 proto tcp
ufw allow in on wg0 from 10.100.0.0/24 to any port 7946 proto tcp
ufw allow in on wg0 from 10.100.0.0/24 to any port 7946 proto udp
ufw allow in on wg0 from 10.100.0.0/24 to any port 4789 proto udp

# Edge (apenas no kvm8)
ufw allow 80/tcp
ufw allow 443/tcp

ufw enable
```

## NFS

### Server (kvm8)

```bash
sudo apt-get install -y nfs-kernel-server
sudo mkdir -p /srv/nfs/swarm_data/webhook_jobs
sudo chmod 0777 /srv/nfs/swarm_data/webhook_jobs
```

`/etc/exports` (exemplo simples para demo):

```
/srv/nfs/swarm_data 10.100.0.0/24(rw,sync,no_subtree_check,fsid=0,no_root_squash)
```

```bash
sudo exportfs -ra
```

### Clients (kvm2/kvm4/kvm8)

```bash
sudo apt-get install -y nfs-common
sudo mkdir -p /mnt/nfs
```

`/etc/fstab`:

```
10.100.0.8:/ /mnt/nfs nfs4 rw,vers=4.2,_netdev,noatime 0 0
```

```bash
sudo mount -a
```

O path usado pelo webhook é:

```
/mnt/nfs/webhook_jobs
```

## Swarm bootstrap

No `kvm8`:

```bash
docker swarm init --advertise-addr 10.100.0.8
```

Nos demais nós (como manager):

```bash
docker swarm join --token <TOKEN> 10.100.0.8:2377
```

Crie as redes e o label do nó fixo:

```bash
just swarm-networks
just swarm-label-kvm8
```

## Secrets do Swarm

```bash
. .env
printf '%s' "$GITHUB_WEBHOOK_SECRET" | docker secret create github_webhook_secret -
printf '%s' "$POSTGRES_PASSWORD" | docker secret create postgres_password -
```

## Deploy do stack

No `kvm8` (ou em qualquer manager):

```bash
just stack-deploy
```

Isso roda:

```
docker stack deploy -c docker/stack.yaml dockerswarmp1 --with-registry-auth
```

O `--with-registry-auth` evita divergência de imagens entre nós.

## Webhook watcher (kvm8)

O API recebe o webhook e cria um arquivo em `/mnt/nfs/webhook_jobs`.
O watcher lê esse diretório e dispara `just stack-deploy`.

Instalar e subir o serviço:

```bash
just watcher-install
```

Acompanhar logs:

```bash
just watcher-logs
```

## Endpoints

- `https://<APP_DOMAIN>/` (frontend)
- `https://<APP_DOMAIN>/api/visit`
- `https://<APP_DOMAIN>/api/webhook/github`

## Comandos úteis

```bash
just stack-services
just stack-ps
just stack-logs api
just stack-logs traefik
```

## Problemas comuns

- Traefik reclamando de API antiga: garanta `DOCKER_API_VERSION=1.53` no serviço Traefik.
- GHCR digest warning no deploy: rode `docker login ghcr.io` e use `--with-registry-auth`.
- Postgres 18 reclamando de volume antigo: use volume em `/var/lib/postgresql` (stack já usa) ou faça `pg_upgrade`.
- Webhook retorna 404: use `/api/webhook/github` e confirme `APP_DOMAIN` + labels do Traefik.
- Webhook permission denied: garanta permissão de escrita no NFS (`/srv/nfs/swarm_data/webhook_jobs`).
- API retorna 503 em `/api/visit`: confirme Postgres no ar e secrets criados.

## Local Run

Docker Compose (mais rápido):

```bash
cp .env.example .env
docker compose -f docker/compose.yaml --env-file .env up --build
```

Ou com `just`:

```bash
just upb
```

A API ficará disponível em:

- `http://localhost:8000/`
- `http://localhost:8000/health`
- `http://localhost:8000/api/visit` (retorna 503 sem Postgres)

Python (sem Docker):

```bash
cp .env.example .env
uv sync
GITHUB_WEBHOOK_SECRET=local uv run uvicorn src.dockerswarmp1.main:app --reload --host 0.0.0.0 --port 8000
```
