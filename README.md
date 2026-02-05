# dockerswarmp1

## Local Run

Docker Compose (fastest):

```bash
cp .env.example .env
docker compose -f docker/compose.yaml --env-file .env up --build
```

Or with `just`:

```bash
just upb
```

The API will be available at:

- `http://localhost:8000/`
- `http://localhost:8000/health`

Python (no Docker):

```bash
cp .env.example .env
uv sync
GITHUB_WEBHOOK_SECRET=local uv run uvicorn src.dockerswarmp1.main:app --reload --host 0.0.0.0 --port 8000
```

## Nodes

| Node | Public IP | WireGuard IP | Domain |
| --- | --- | --- | --- |
| kvm2 | 76.13.71.178 | 10.100.0.2 | inprod.cloud |
| kvm4 | 191.101.70.130 | 10.100.0.4 | otaviomiranda.cloud |
| kvm8 | 89.116.73.152 | 10.100.0.8 | myswarm.cloud |

Notes

- Only `kvm8` is exposed to the public internet (Traefik edge).
- `app.myswarm.cloud` is the single public domain for frontend and API.
- `kvm2` and `kvm4` are locked down by the firewall.

## Swarm Prerequisites

Create the overlay networks before deploying the stack:

```bash
docker network create --driver=overlay --attachable public
docker network create --driver=overlay --attachable --internal internal
```

Label the KVM8 node (for fixed services):

```bash
docker node update --label-add role=kvm8 kvm8
```

Create Swarm secrets (run on a manager, e.g. KVM8):

```bash
. .env
printf '%s' "$GITHUB_WEBHOOK_SECRET" | docker secret create github_webhook_secret -
printf '%s' "$POSTGRES_PASSWORD" | docker secret create postgres_password -
```

## Webhook Watcher (KVM8)

The webhook endpoint writes job files into `/mnt/nfs/webhook_jobs`. The watcher
checks this folder and triggers a deploy (debounced).

Install and run:

```bash
just watcher-install
```

Follow logs:

```bash
just watcher-logs
```

Service file used by systemd:

- `/opt/dockerswarmp1/scripts/webhook-watcher.service`

## NFS (KVM8)

Server export (`/etc/exports` on KVM8):

```
/srv/nfs/swarm_data 10.100.0.0/24(rw,sync,no_subtree_check,fsid=0)
```

Client mount (`/etc/fstab` on all nodes):

```
10.100.0.8:/ /mnt/nfs nfs4 rw,vers=4.2,_netdev,noatime 0 0
```

Shared path for the API webhook jobs:

```
/mnt/nfs/webhook_jobs
```
