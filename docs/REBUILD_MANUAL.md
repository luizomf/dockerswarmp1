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
- Se voce remover `kvm4` e `kvm2`, voce fica com **1 manager** (`kvm8`).
  Isso e OK por pouco tempo (durante a formatacao), mas voce perde tolerancia a falhas.
- Se precisar "forcar" remocao de node, faca isso consciente: `docker node rm --force`.

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

## Recriar o Swarm (quando os nos voltarem)

No `kvm8`:

```bash
docker swarm init --advertise-addr 10.100.0.8
```

Nos outros (como manager):

```bash
docker swarm join --token <TOKEN> 10.100.0.8:2377
```

No repositorio (no `kvm8`):

```bash
cd /opt/dockerswarmp1
just swarm-networks
just swarm-label-kvm8
```

## Secrets, GHCR e deploy

Tudo isso esta no `DEV_GUIDE.md` e `README.md`. Ordem recomendada:

1. `docker login ghcr.io ...`
2. criar secrets (`github_webhook_secret`, `postgres_password`)
3. `just stack-deploy`
4. watcher (`just watcher-install`)
