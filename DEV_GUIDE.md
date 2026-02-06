# Developer Guide (Server Bootstrap + Video Prereqs)

Este arquivo existe para manter o `README.md` e o video focados. Aqui ficam os
passos "chatos" (bootstrap e hardening basico) e alguns atalhos para quando
voce for replicar o projeto do zero.

Escopo: baseline com 3 VPS (todos managers) usando Docker Swarm, WireGuard,
Traefik, GHCR, webhook deploy e Postgres.

## Hostinger (publi)

Eu uso as VPS KVM da Hostinger:

- Link: https://hostinger.com/otaviomiranda
- Cupom: `OTAVIOMIRANDA`

## 0) Variaveis que voce vai preencher

Substitua estes valores no guia:

```text
YOUR_PUBLIC_IP            Seu IP (para liberar SSH no UFW)
KVM2_PUBLIC_IP            IP publico do kvm2
KVM4_PUBLIC_IP            IP publico do kvm4
KVM8_PUBLIC_IP            IP publico do kvm8 (edge)
WG_CIDR                   Rede WireGuard (ex: 10.100.0.0/24)
KVM8_WG_IP                IP WireGuard do kvm8 (ex: 10.100.0.8)
APP_DOMAIN                Dominio publico (ex: app.myswarm.cloud)
GITHUB_USER               Seu user do GitHub
GHCR_PAT                  Seu PAT com read:packages (e write:packages se quiser)
```

## 1) OS e pacotes base

Para repetir o video, use um Ubuntu recente (ex: 24.04) e instale Docker.
Na Hostinger, o template "Ubuntu with Docker" ja ajuda.

Em cada VPS:

```bash
sudo apt-get update
sudo apt-get install -y git ufw fail2ban nfs-common
```

No `kvm8` (NFS server):

```bash
sudo apt-get install -y nfs-kernel-server
```

## 2) SSH (minimo seguro)

Recomendacao:

- Crie um usuario nao-root.
- Desabilite login por senha.
- Permita SSH somente por chave.

Checklist rapido:

```bash
sudo adduser luizotavio
sudo usermod -aG sudo,docker luizotavio
```

Edite `/etc/ssh/sshd_config` (exemplo):

```text
PasswordAuthentication no
PermitRootLogin no
```

Reinicie:

```bash
sudo systemctl restart ssh
```

## 3) Fail2ban (sshd)

Em geral, o default ja ajuda. Para ver status:

```bash
sudo fail2ban-client status
sudo fail2ban-client status sshd
```

## 4) WireGuard (rede privada entre os nos)

O projeto assume que os nos se enxergam via WireGuard (ex: `10.100.0.0/24`).

Checklist:

```bash
sudo systemctl enable --now wg-quick@wg0
sudo systemctl status wg-quick@wg0 --no-pager
ip -brief addr show wg0
ping -c 1 10.100.0.8
```

## 5) UFW (baseline simples)

Em cada VPS:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH apenas do seu IP
sudo ufw allow from YOUR_PUBLIC_IP/32 to any port 22 proto tcp

# WireGuard
sudo ufw allow 51820/udp
```

Liberar portas do Swarm apenas na rede WireGuard (`WG_CIDR`):

```bash
sudo ufw allow in on wg0 from WG_CIDR to any port 2377 proto tcp
sudo ufw allow in on wg0 from WG_CIDR to any port 7946 proto tcp
sudo ufw allow in on wg0 from WG_CIDR to any port 7946 proto udp
sudo ufw allow in on wg0 from WG_CIDR to any port 4789 proto udp
```

No `kvm8` (edge), liberar HTTP/HTTPS:

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

Ativar:

```bash
sudo ufw enable
sudo ufw status
```

## 6) NFS (somente para webhook jobs)

Neste baseline, NFS e usado apenas como pasta compartilhada para a fila do
webhook (`webhook_jobs`). Nao e "storage distribuido".

### Server (kvm8)

```bash
sudo mkdir -p /srv/nfs/swarm_data/webhook_jobs
```

`/etc/exports` (demo):

```text
/srv/nfs/swarm_data WG_CIDR(rw,sync,no_subtree_check,fsid=0,no_root_squash)
```

Aplicar:

```bash
sudo exportfs -ra
```

### Clients (todos os nos)

```bash
sudo mkdir -p /mnt/nfs
```

`/etc/fstab` (mais resiliente no boot):

```text
KVM8_WG_IP:/ /mnt/nfs nfs4 rw,vers=4.2,_netdev,noatime,nofail,x-systemd.automount,x-systemd.idle-timeout=600,x-systemd.device-timeout=10s,x-systemd.mount-timeout=30s,x-systemd.requires=wg-quick@wg0.service 0 0
```

Montar:

```bash
sudo mount -a
findmnt /mnt/nfs
```

### Permissoes (API uid/gid 1011 + watcher)

O container da API escreve com UID/GID `1011`. Para o watcher (host) conseguir
apagar os arquivos, alinhe grupo e defaults:

Em todos os nos:

```bash
sudo groupadd -g 1011 app || true
sudo usermod -aG app luizotavio
```

No `kvm8` (server NFS):

```bash
sudo chown -R root:app /srv/nfs/swarm_data/webhook_jobs
sudo chmod 2770 /srv/nfs/swarm_data/webhook_jobs
sudo setfacl -R -m g:app:rwx /srv/nfs/swarm_data/webhook_jobs
sudo setfacl -R -m d:g:app:rwx /srv/nfs/swarm_data/webhook_jobs
```

Teste rapido (no `kvm8`):

```bash
sudo -u luizotavio mktemp -p /mnt/nfs/webhook_jobs perm_test.XXXXXX
```

## 7) Swarm bootstrap

No `kvm8`:

```bash
docker swarm init --advertise-addr KVM8_WG_IP
```

Nos demais (como manager):

```bash
docker swarm join --token <TOKEN> KVM8_WG_IP:2377
```

No repositorio (em um manager, ex: `kvm8`):

```bash
cd /opt/dockerswarmp1
just swarm-networks
just swarm-label-kvm8
```

## 8) GHCR auth

O Swarm vai dar pull das imagens do GHCR. No minimo, faca login no `kvm8`:

```bash
docker login ghcr.io -u GITHUB_USER -p GHCR_PAT
```

## 9) Deploy (manual) e watcher

No repositorio:

```bash
cd /opt/dockerswarmp1
cp .env.example .env
```

Preencha `.env` com `APP_DOMAIN`, `EMAIL`, `POSTGRES_*`, `GITHUB_WEBHOOK_SECRET`.

Crie secrets:

```bash
. .env
printf '%s' "$GITHUB_WEBHOOK_SECRET" | docker secret create github_webhook_secret -
printf '%s' "$POSTGRES_PASSWORD" | docker secret create postgres_password -
```

Deploy:

```bash
just stack-deploy
```

Watcher (kvm8):

```bash
just watcher-install
just watcher-logs
```

