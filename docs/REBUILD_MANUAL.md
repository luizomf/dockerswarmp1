# Rebuild Manual (Format -> Bootstrap -> Deploy)

Este manual e para quando voce vai refazer as VPS do zero e quer uma ordem
segura e reproduzivel. Ele complementa (e nao substitui) `DEV_GUIDE.md`.

Objetivo:

- refazer um cluster Swarm pequeno (3 VPS) sem se trancar fora
- evitar downtime desnecessario
- manter o processo "gravavel" para o video

Escopo:

- baseline com 3 VPS (kvm2, kvm4, kvm8)
- todos os nos como managers (na demo)
- `kvm8` e o edge publico e hospeda NFS/Postgres

## Regras de ouro

- Formate `kvm2` e `kvm4` primeiro. Deixe o `kvm8` por ultimo.
- Remova **um no por vez** do Swarm.
- Drenar ou reiniciar o `kvm8` derruba o app (Traefik + Postgres + NFS estao
  fixos nele). Planeje janela e avise no video.
- Se voce remover `kvm4` e `kvm2`, voce fica com **1 manager** (`kvm8`). Isso e
  OK por pouco tempo (durante a formatacao), mas voce perde tolerancia a falhas.
- Se precisar "forcar" remocao de node, faca isso consciente:
  `docker node rm --force`.

## Checklist pre-format (na sua maquina, fora das VPS)

- Acesso ao painel/console da Hostinger (para recuperar se UFW/SSH travar).
- Salvar:
  - configs e chaves do WireGuard de cada no (`wg0.conf`)
  - sua chave SSH (privada) e `authorized_keys`
  - valores de secrets (nao cole no repo):
    - `GITHUB_WEBHOOK_SECRET`
    - `POSTGRES_PASSWORD`
    - PAT do GHCR (ex: `read:packages`)
- Anotar:
  - IP publico + hostname + IP WireGuard (`10.100.0.x`) de cada no
  - dominio final apontando para o `kvm8` (ex: `app.myswarm.cloud`)

## Manutencao: drenar e remover um no do Swarm (antes de formatar)

### 1) No manager (ex: `kvm8`)

```bash
docker node ls
docker node update --availability drain <NODE>
docker node ps <NODE>
docker stack ps dockerswarmp1
```

Espere o `<NODE>` ficar sem tasks (ou so `Shutdown/Complete`).

### 2) Ainda no manager: remover do Raft (demote)

```bash
docker node demote <NODE>
docker node ls
```

### 3) No proprio node: sair do swarm

```bash
docker swarm leave
```

### 4) No manager: remover o node do cluster

```bash
docker node rm <NODE>
```

### Exemplo real (feito no video): removendo o `kvm2`

No `kvm8`:

```bash
docker node update --availability drain kvm2
docker node ps kvm2
docker node demote kvm2
```

No `kvm2`:

```bash
docker swarm leave
```

No `kvm8`:

```bash
docker node rm kvm2
```

### Repetir para o `kvm4`

Sim, o mesmo fluxo.

Atencao: ao remover `kvm4` voce ficara com apenas 1 manager (`kvm8`). Evite
parar o `kvm8` ate o cluster estar reconstruido.

## Manutencao: remover o ultimo node (`kvm8`) antes de formatar

Quando `kvm2` e `kvm4` ja foram removidos, o Swarm fica "sozinho" no `kvm8`.
Antes de formatar o `kvm8`, o mais limpo e:

1. parar o watcher (systemd) se estiver instalado
2. remover a stack (services)
3. remover secrets e networks (opcional, mas deixa o host mais "limpo")
4. sair do swarm

### 0) Validar que so existe o `kvm8`

No `kvm8`:

```bash
docker node ls
docker stack ls
docker stack services dockerswarmp1
```

### 1) Parar o watcher (se existir)

No `kvm8`:

```bash
cd /opt/dockerswarmp1
just watcher-uninstall
```

Ou manual (se preferir):

```bash
sudo systemctl disable --now webhook-watcher || true
sudo rm -f /etc/systemd/system/webhook-watcher.service
sudo systemctl daemon-reload
```

### 2) Remover a stack

No `kvm8`:

```bash
docker stack rm dockerswarmp1
```

Espere limpar:

```bash
docker stack ls
docker service ls
```

### 3) (Opcional) Remover networks overlay e secrets

Se voce quer deixar o host "limpo" antes de formatar:

```bash
docker secret ls
docker secret rm github_webhook_secret postgres_password || true

docker network ls
docker network rm public internal || true
```

### 4) Sair do Swarm (ultimo manager)

No `kvm8`:

```bash
docker swarm leave --force
```

Validacao:

```bash
docker info | grep -n "Swarm:"
```

## Post-format (resumo) por no

Para detalhes e comandos: veja `DEV_GUIDE.md`.

Checklist rapido:

- SSH por chave (evitar lockout)
- UFW: liberar SSH do seu IP antes de `ufw enable`
- fail2ban habilitado
- Docker instalado e funcionando
- WireGuard funcionando (todos pingam `10.100.0.x`)

## NFS (webhook_jobs) antes do deploy

O stack usa `/mnt/nfs/webhook_jobs` (bind mount) para a fila do webhook ser
compartilhada entre os nos. Antes de fazer `stack-deploy`, garanta que:

- o NFS server esta exportando no `kvm8`
- todos os nos montam NFS em `/mnt/nfs`
- `/mnt/nfs/webhook_jobs` existe e e gravavel

Para detalhes, veja a secao de NFS no `DEV_GUIDE.md`. Resumo rapido:

Server (`kvm8`):

```bash
sudo apt-get install -y nfs-kernel-server
sudo mkdir -p /srv/nfs/swarm_data/webhook_jobs

# Permissoes (uid/gid 1011)
sudo groupadd -g 1011 app || true
sudo usermod -aG app "$USER" || true
sudo chown -R root:app /srv/nfs/swarm_data/webhook_jobs
sudo chmod 2770 /srv/nfs/swarm_data/webhook_jobs
sudo setfacl -R -m g:app:rwx /srv/nfs/swarm_data/webhook_jobs
sudo setfacl -R -m d:g:app:rwx /srv/nfs/swarm_data/webhook_jobs

# Importante: depois de `usermod -aG ...`, sua sessao SSH atual nao pega o grupo
# novo. Faça relogin ou rode: `newgrp app`.
# Para confirmar: `id -nG | tr ' ' '\n' | grep -x app`.

EXPORT_LINE="/srv/nfs/swarm_data 10.100.0.0/24(rw,sync,no_subtree_check,fsid=0,no_root_squash)"
sudo grep -qF "$EXPORT_LINE" /etc/exports || echo "$EXPORT_LINE" | sudo tee -a /etc/exports
sudo exportfs -ra
```

Clients (kvm2/kvm4/kvm8):

Importante: sim, o `kvm8` tambem precisa montar `/mnt/nfs` (mesmo sendo o NFS
server). Caso contrario o watcher falha com:

```text
mkdir: cannot create directory '/mnt/nfs': Permission denied
```

```bash
sudo apt-get install -y nfs-common
sudo mkdir -p /mnt/nfs

# Alinhar grupo usado pelos containers (somente necessario se voce for mexer
# nesses arquivos pelo host).
sudo groupadd -g 1011 app || true
sudo usermod -aG app "$USER" || true
```

Nota:

- Mesmo detalhe do server: faça relogin ou `newgrp app` para a permissao do
  grupo passar a valer na sessao atual.

`/etc/fstab` (mais resiliente no boot):

```bash
sudo vim /etc/fstab
10.100.0.8:/ /mnt/nfs nfs4 rw,vers=4.2,_netdev,noatime,nofail,x-systemd.automount,x-systemd.idle-timeout=600,x-systemd.device-timeout=10s,x-systemd.mount-timeout=30s,x-systemd.requires=wg-quick@wg0.service 0 0
sudo systemctl daemon-reload
```

Montar e validar:

```bash
sudo mount -a
findmnt /mnt/nfs
mktemp -p /mnt/nfs/webhook_jobs perm_test.XXXXXX
```

Validacao adicional (antes do watcher):

```bash
ls -ld /mnt/nfs/webhook_jobs
sudo -u "$USER" mktemp -p /mnt/nfs/webhook_jobs watcher_perm_test.XXXXXX
sudo -u "$USER" rm -f /mnt/nfs/webhook_jobs/watcher_perm_test.*
```

## Nota importante: aperte o UFW depois do WireGuard

Para este projeto, Swarm e NFS devem trafegar pelo WireGuard, nao pela internet.

O que procurar:

- Se `ufw status` mostrar regras do tipo "allow from <IP publico do node> to
  port 2377/7946/4789/2049", isso significa que voce esta permitindo Swarm/NFS
  via internet (mesmo que o edge firewall filtre).

Baseline recomendado:

- manter `22/tcp` apenas do seu IP
- manter `51820/udp` aberto
- permitir Swarm/NFS somente `in on wg0 from 10.100.0.0/24`
- no `kvm8`, abrir `80/443` para Traefik

Proximo ajuste (quando o WireGuard estiver 100% ok):

- se hoje voce ainda tem regras de Swarm/NFS liberadas por IP publico, aperte o
  UFW para permitir essas portas apenas via `wg0` (e manter o resto fechado). Eu
  so faria isso quando voce disser "pode apertar agora", porque e a hora que
  mais da lockout se uma regra estiver errada.

Se voce quiser ajustar rapido (com cuidado para nao se trancar fora):

1. garanta que existe uma regra para seu SSH (seu IP) antes de mexer no resto
2. `sudo ufw reset` e reaplique as regras do `DEV_GUIDE.md` /
   `scripts/vps_bootstrap`

Para uma migracao "incremental" (sem reset), veja o passo-a-passo em
`docs/VPS_BOOTSTRAP.md` ("Apertar UFW (migracao para wg0-only)").

## Recriar o Swarm (quando os nos voltarem)

No `kvm8`:

```bash
docker swarm init --advertise-addr 10.100.0.8
```

Nos outros (como manager):

```bash
docker swarm join --token <TOKEN> 10.100.0.8:2377
```

## Baixar o repositorio (kvm8)

O repositorio precisa existir no `kvm8` antes de usar `just`.

```bash
sudo mkdir -p /opt/dockerswarmp1
sudo chown -R "$USER:$USER" /opt/dockerswarmp1

git clone git@github.com:luizomf/dockerswarmp1.git /opt/dockerswarmp1
```

Se voce nao usa SSH no GitHub, troque por HTTPS:

```bash
git clone https://github.com/luizomf/dockerswarmp1.git /opt/dockerswarmp1
cp .env.example
```

No repositorio (no `kvm8`):

```bash
cd /opt/dockerswarmp1
just swarm-networks
just swarm-label-kvm8
```

## Secrets, GHCR e deploy

Objetivo: deixar o deploy "rodavel" sem sair deste arquivo.

Ordem recomendada (no `kvm8`):

1. preparar `.env`
2. login no GHCR (comandos mais abaixo)
3. criar secrets no Swarm
4. deploy do stack
5. Validação (curl + logs)
6. watcher (auto deploy)

Os secrets do docker swarm para essa aplicação são: `github_webhook_secret` e
`postgres_password`.

Os secrets das actions são: `DEPLOY_WEBHOOK_SECRET` (mesmo valor do
`github_webhook_secret`) e `DEPLOY_WEBHOOK_URL` (URL do Webhook).

Em nosso caso, a URL do webhook é `https://<DOMINIO>/api/webhook/github`.

### 1) Preparar `.env` (kvm8)

No `kvm8`:

```bash
cd /opt/dockerswarmp1
cp .env.example .env
vim .env
```

Preencha (nao cole no repo):

- `EMAIL`
- `APP_DOMAIN` (ex: `app.myswarm.cloud`)
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `GITHUB_WEBHOOK_SECRET`

Opcional:

- `VISIT_SALT` (fallback para gerar o hash anonimo de visitas)

### 2) Login no GHCR (kvm8)

No minimo, faca login no `kvm8` e use `--with-registry-auth` no deploy.

Interactive:

```bash
docker login ghcr.io
```

Ou via PAT (melhor para gravar):

```bash
echo "$GHCR_PAT" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin
```

### 3) Criar secrets no Swarm (kvm8)

No `kvm8`:

```bash
cd /opt/dockerswarmp1
. .env

printf '%s' "$GITHUB_WEBHOOK_SECRET" | docker secret create github_webhook_secret -
printf '%s' "$POSTGRES_PASSWORD" | docker secret create postgres_password -
```

Validar:

```bash
docker secret ls
```

### 4) Deploy do stack (kvm8)

No `kvm8`:

```bash
cd /opt/dockerswarmp1
just stack-deploy
```

Nota importante sobre `.env`:

- `docker stack deploy` **nao** le `.env` automaticamente.
- O `just` funciona porque exporta as variaveis do `.env` antes de rodar.
- Se voce rodar o `docker stack deploy` "na mao", faca isso:

```bash
cd /opt/dockerswarmp1
set -a
. .env
set +a
docker stack deploy -c docker/stack.yaml dockerswarmp1 --with-registry-auth
```

Se `APP_DOMAIN` estiver vazio, o Traefik vai tentar `Host(\`\`)` e falhar no ACME.

Validar:

```bash
docker stack services dockerswarmp1
docker stack ps dockerswarmp1
```

### 5) Validacao rapida (kvm8 / sua maquina)

```bash
curl -fsS "https://app.myswarm.cloud/" | head -n 5
curl -fsS "https://app.myswarm.cloud/api/visit"
```

Teste externo (para simular outro IP e ver o contador subir):

- rode um "website test" gratuito (ex: Lighthouse online, PageSpeed, etc.)
- isso gera requests reais de outros IPs
- depois recarregue a home e confira o numero de "Visitas Hoje (unicas)"

Se a API nao subir, veja logs:

```bash
cd /opt/dockerswarmp1
just stack-logs api
just stack-logs postgres
just stack-logs traefik
```

### 6) Watcher (auto deploy) no `kvm8`

No `kvm8`:

```bash
cd /opt/dockerswarmp1
just watcher-install
just watcher-logs
```

Se der `Permission denied` no `rm` da fila em `/mnt/nfs/webhook_jobs`:

- confirme que o NFS esta com `root:app` + `2770` + ACL default
- confirme que o user do watcher (ex: `luizotavio`) esta no grupo `app`
- depois de `usermod -aG app ...`, faca relogin ou `newgrp app`
