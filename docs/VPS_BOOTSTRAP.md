# VPS Bootstrap - Segurança básica

```bash
# No servidor
# Primeiro login com root (o VPS já veio com Docker instalado)
USERNAME=luizotavio ; useradd -m -s /bin/bash $USERNAME \
  && usermod -aG sudo $USERNAME \
  && usermod -aG docker $USERNAME \
  && passwd $USERNAME \
  && su $USERNAME

# No seu computador (assumindo que você já tema chave SSH)
# ssh-copy-id -i ~/.ssh/id_SUA_CHAVE.pub USERNAME@HOST_OU_IP_DO_VPS

# ssh-copy-id -i ~/.ssh/id_hostinger.pub luizotavio@inprod.cloud # kvm2
# ssh-copy-id -i ~/.ssh/id_hostinger.pub luizotavio@otaviomiranda.cloud # kvm4
# ssh-copy-id -i ~/.ssh/id_hostinger.pub luizotavio@myswarm.cloud # kvm8
```

---

## Regras no firewall de borda (hpanel)

Isso é no hpanel da Hostinger:

```
ACTION   PROTOCOL  PORT(S)     SOURCE           SOURCE_DETAIL
Accept   TCP       Any         Custom           187.108.118.25
Accept   TCP       Any         Custom           89.116.73.152
Accept   TCP       Any         Custom           191.101.70.130
Accept   TCP       Any         Custom           76.13.71.178

Accept   UDP       4789        Custom           76.13.71.178
Accept   UDP       4789        Custom           191.101.70.130
Accept   UDP       4789        Custom           89.116.73.152

Accept   UDP       7946        Custom           89.116.73.152
Accept   UDP       7946        Custom           191.101.70.130
Accept   UDP       7946        Custom           76.13.71.178

Accept   ICMP      Any         Custom           191.101.70.130
Accept   ICMP      Any         Custom           76.13.71.178
Accept   ICMP      Any         Custom           89.116.73.152

Accept   HTTPS     443         Any              Any
Accept   HTTP      80          Any              Any

Accept   UDP       51820       Custom           191.101.70.130
Accept   UDP       51820       Custom           89.116.73.152
Accept   UDP       51820       Custom           187.108.118.25
Accept   UDP       51820       Custom           76.13.71.178

Accept   TCP       8080        Custom           187.108.118.25
Accept   ICMP      Any         Custom           187.108.118.25

Drop     Any       Any         Any              Any
```

- **4789/UDP** → Docker Swarm overlay (VXLAN)
- **7946/UDP** → Swarm gossip (node discovery)
- **51820/UDP** → WireGuard
- **TCP Any (Custom IPs)** → comunicação entre nós (provavelmente Swarm
  manager/worker + SSH hardening externo)
- **ICMP liberado apenas entre nós e IP específico**
- **HTTP/HTTPS abertos ao mundo**
- **Drop all no final** → firewall default deny (correto)

Nota:
- Se voce vai rodar Swarm e NFS **por dentro do WireGuard** (recomendado neste projeto),
  nao precisa expor `2377/7946/4789/2049` na internet. Basta `51820/udp` entre os nos,
  e `80/443` no edge (`kvm8`). O UFW vai permitir essas portas apenas via `wg0`.

---

## Script restante para VPS

Este script deve ser executado no seu usuário (não como root).

- [../scripts/vps_bootstrap](../scripts/vps_bootstrap)

---

## Notas de segurança (importante)

- O script desabilita autenticação por senha e root no SSH. Garanta que sua
  chave já está em `~/.ssh/authorized_keys` antes de rodar, senão você pode se
  trancar fora.
- `NOPASSWD sudo` é opcional e **vem desativado**. Se você ativar (para facilitar
  bootstrap), remova depois.

Variáveis úteis (exemplos):

```bash
# admin IP para SSH
export ADMIN_SSH_CIDR="187.108.118.25/32"

# rede do WireGuard (Swarm e NFS passam por aqui)
export WG_CIDR="10.100.0.0/24"
export WG_INTERFACE="wg0"

# edge node (kvm8): abre 80/443
export IS_EDGE_NODE=1

# somente se você quiser NOPASSWD temporariamente
export ENABLE_NOPASSWD_SUDO=1

# se você for rerodar o script e não quiser ficar fazendo upgrade toda vez
export ENABLE_APT_UPGRADE=0

# se você já configurou UFW e só quer "garantir as regras", sem resetar tudo
export ENABLE_UFW_RESET=0

./scripts/vps_bootstrap
```

Para remover `NOPASSWD` depois:

```bash
export ENABLE_NOPASSWD_SUDO=0
./scripts/vps_bootstrap
```

---

## Checklist de validacao (pos-bootstrap + pos-WireGuard)

Rode em cada VPS e confira se "bate" com o esperado.

WireGuard:

```bash
ip -brief addr show wg0
sudo wg show
```

Esperado:
- `wg0` com IP correto (`10.100.0.2/24`, `10.100.0.4/24`, `10.100.0.8/24`)
- `latest handshake` recente com os peers

SSH hardening (config efetiva):

```bash
sudo sshd -T | egrep -i "(passwordauthentication|permitrootlogin|kbdinteractiveauthentication|usepam|allowtcpforwarding|allowagentforwarding|allowstreamlocalforwarding|maxauthtries|logingracetime)" | sort
```

UFW:

```bash
sudo ufw status verbose
```

Esperado (baseline do projeto):
- `22/tcp` permitido apenas do seu IP (`ADMIN_SSH_CIDR`)
- `51820/udp` (WireGuard) permitido
- Swarm/NFS permitidos apenas via WireGuard (`in on wg0 from 10.100.0.0/24`)
- Somente no `kvm8`: `80/tcp` e `443/tcp` permitidos

Se hoje voce ainda estiver com regras de Swarm/NFS liberadas por IP publico, o
proximo ajuste e "apertar" isso para apenas `wg0` quando o WireGuard estiver
estavel (veja `docs/REBUILD_MANUAL.md`).

### Apertar UFW (migracao para wg0-only)

Se voce ja tem regras antigas liberando Swarm/NFS por IP publico, a migracao
segura e:

1. adicionar as regras `on wg0` primeiro
2. remover as regras antigas
3. validar com `ufw status verbose`

Exemplo (ajuste os IPs para o seu ambiente):

```bash
# 1) adicionar regras via wg0
sudo ufw allow in on wg0 from 10.100.0.0/24 to any port 2377 proto tcp
sudo ufw allow in on wg0 from 10.100.0.0/24 to any port 7946 proto tcp
sudo ufw allow in on wg0 from 10.100.0.0/24 to any port 7946 proto udp
sudo ufw allow in on wg0 from 10.100.0.0/24 to any port 4789 proto udp

# no kvm8 (NFS server)
sudo ufw allow in on wg0 from 10.100.0.0/24 to any port 2049 proto tcp

# no kvm8 (edge)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 2) remover regras antigas (exemplo)
sudo ufw delete allow from <KVM2_PUBLIC_IP> to any port 2377 proto tcp
sudo ufw delete allow from <KVM2_PUBLIC_IP> to any port 7946 proto tcp
sudo ufw delete allow from <KVM2_PUBLIC_IP> to any port 7946 proto udp
sudo ufw delete allow from <KVM2_PUBLIC_IP> to any port 4789 proto udp

# 3) validar
sudo ufw status verbose
```

Fail2ban:

```bash
sudo systemctl is-active fail2ban
sudo fail2ban-client status sshd
```

NOPASSWD sudo (temporario):

```bash
sudo grep -R "NOPASSWD" -n /etc/sudoers.d || true
```

Se aparecer `NOPASSWD`, ok durante o bootstrap, mas lembre de remover ao final.

## WireGuard (Semi)

Nota importante:
- Cada VPS tem **um** arquivo `wg0.conf` e ele deve ter **um** bloco `[Interface]`.
- O exemplo abaixo mostra blocos separados (um por VPS) para referencia. Nao copie
  3x `[Interface]` no mesmo arquivo.

```
[Interface]
Address = 10.100.0.8/24 # The internal IP of this VPS
ListenPort = 51820 # The port
PrivateKey = THIS_VPS_PRIVATE_KEY # The private key of this VPS

[Interface]
Address = 10.100.0.4/24 # The internal IP of this VPS
ListenPort = 51820 # The port
PrivateKey = THIS_VPS_PRIVATE_KEY # The private key of this VPS

[Interface]
Address = 10.100.0.2/24 # The internal IP of this VPS
ListenPort = 51820 # The port
PrivateKey = THIS_VPS_PRIVATE_KEY # The private key of this VPS

[Peer]
PublicKey = PEER_PUBLIC_KEY # The public key of the other VPS
AllowedIPs = 10.100.0.8/32 # The internal IP Addres of the other VPS
Endpoint = PEER_PUBLIC_IP_ADDRESS:51820 # The public ip addres of the other VPS
PersistentKeepalive = 25

[Peer]
PublicKey = PEER_PUBLIC_KEY # The public key of the other VPS
AllowedIPs = 10.100.0.4/32 # The internal IP Addres of the other VPS
Endpoint = PEER_PUBLIC_IP_ADDRESS:51820 # The public ip addres of the other VPS
PersistentKeepalive = 25

[Peer]
PublicKey = PEER_PUBLIC_KEY # The public key of the other VPS
AllowedIPs = 10.100.0.2/32 # The internal IP Addres of the other VPS
Endpoint = PEER_PUBLIC_IP_ADDRESS:51820 # The public ip addres of the other VPS
PersistentKeepalive = 25
```

---
