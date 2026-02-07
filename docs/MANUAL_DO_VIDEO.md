# Manual do Vídeo: Cluster Docker Swarm na Hostinger

Este documento é um registro fiel e passo a passo de todas as etapas executadas no vídeo para subir o cluster Docker Swarm.

> **Nota:** Este guia assume que você tem 3 VPS na Hostinger (KVM 2 ou superior) e um domínio configurado.

## Status Atual
- [ ] VPS Formatadas
- [ ] Acesso SSH Inicial
- [ ] Configuração de Rede
- [ ] Swarm Init
- [ ] Deploy

## 0. Preparação e Desmontagem (Opcional)

Caso você já tenha um cluster rodando e queira remover um nó de forma segura para formatá-lo (como estamos fazendo com o `kvm2`), siga estes passos. Isso garante que os serviços sejam migrados para outros nós antes do desligamento.

**No nó gerenciador principal (ex: `kvm8`):**

1. **Drenar o nó (`Drain`):**
   Isso remove todos os contêineres em execução neste nó e os move para outros nós disponíveis. Também impede que novas tarefas sejam agendadas nele.
   ```bash
   docker node update kvm2 --availability drain
   ```

2. **Rebaixar para Worker (`Demote`):**
   Se o nó for um Manager, é uma boa prática rebaixá-lo para Worker antes de removê-lo. Isso ajuda a manter o quórum do Swarm estável.
   ```bash
   docker node demote kvm2
   ```

**No nó que será removido (ex: `kvm2`):**

3. **Sair do Cluster:**
   Este comando remove o nó do Swarm e limpa o estado local do Docker Swarm.
   ```bash
   docker swarm leave
   ```

> **Nota:** Repita este mesmo processo para outros nós secundários (como o `kvm4`), deixando o nó principal (`kvm8`) por último.

**De volta ao nó principal (ex: `kvm8`):**

4. **Remover metadados dos nós antigos:**
   Após os nós saírem, eles ficam listados como "Down". Precisamos removê-los da lista do gerenciador.
   ```bash
   docker node rm kvm4
   docker node rm kvm2
   ```

5. **Verificar o estado do Cluster:**
   Neste momento, o `kvm8` é o único nó restante. Ele é crítico pois segura nosso Banco de Dados, o NFS e é a porta de entrada (Traefik).
   
   Confira se os nós sumiram e o estado atual dos serviços:
   ```bash
   # Deve listar apenas o kvm8 como ativo (Ready/Active)
   docker node ls
   
   # Verifique suas stacks
   docker stack ls
   
   # Verifique onde os serviços estão rodando (agora tudo deve estar tentando ir para o kvm8 ou falhando se não houver recursos)
   docker stack services dockerswarmp1
   ```

6. **Remover a Stack:**
   Agora que verificamos tudo, vamos remover a stack (o conjunto de aplicações) para garantir que nada fique pendurado ou escrevendo no disco enquanto desligamos.
   ```bash
   docker stack rm dockerswarmp1
   ```
   *(Aguarde alguns instantes para que os containers sejam parados)*

7. **Destruir o Cluster (Swarm Leave Force):**
   Como este é o último gerenciador (Leader), ele não pode simplesmente "sair" (`leave`). Precisamos forçar o encerramento do cluster. **Atenção: Isso apaga todas as configurações do Swarm, segredos e serviços.**
   ```bash
   docker swarm leave --force
   ```

   **Pronto!** O cluster foi desmontado. Agora as máquinas são apenas VPSs comuns com Docker instalado (ou prontas para serem formatadas).

## 1. Formatação (Reset Total)

Para garantir um ambiente limpo, formatamos todas as 3 VPSs (`kvm2`, `kvm4`, `kvm8`) usando o painel da Hostinger.

**No hPanel:**
1. Acesse **VPS** > **Gerenciar** (em cada nó).
2. Vá em **SO e Painel** > **Sistema Operacional** > **Mudar SO**.
3. Escolha **SO com Aplicativo** e procure por **Docker** (Ubuntu 24.04).
4. Defina uma senha forte para o `root`.

> **Nota:** Existe um vídeo anterior detalhando exaustivamente este processo de criação de VPS. Aqui, usamos a imagem pronta "Ubuntu 24.04 with Docker" para ganhar tempo e garantir que o Docker Engine já venha instalado e configurado corretamente.

## 2. Configuração de Hostname e DNS

Acesse cada VPS via SSH (inicialmente como `root`, usando a senha definida na formatação) e configure a identidade da máquina.

> **Dica de Acesso Rápido:**
> No próprio hPanel, existe um botão **Terminal** (no topo direito da gestão da VPS). Ele abre um console web já logado como `root` (sem precisar de senha ou chave SSH configurada). É extremamente útil para esses ajustes iniciais antes de configurarmos o nosso acesso SSH definitivo.

**Exemplo no `kvm2`:**

1.  **Definir o Hostname:**
    ```bash
    hostnamectl set-hostname kvm2
    ```

2.  **Ajustar Hosts:**
    Edite o arquivo para associar o IP local ao novo nome e domínio (FQDN).
    ```bash
    vim /etc/hosts
    ```
    Alterar a linha `127.0.1.1` (ou similar) para ficar assim:
    ```text
    127.0.1.1       kvm2.inprod.cloud       kvm2
    ```

> **Atenção aos Domínios:**
> No vídeo, usamos 3 domínios reais diferentes que já possuem apontamentos DNS (Tipo A) criados na Cloudflare apontando para os IPs das VPSs. **Você precisará dos seus próprios domínios ou subdomínios.**
>
> **Mapa da Demo:**
> | Hostname | Domínio | IP Externo | IP VPN (WireGuard) | Usuário SSH |
> | :--- | :--- | :--- | :--- | :--- |
> | **kvm2** | `inprod.cloud` | `76.13.71.178` | `10.100.0.2/24` | `luizotavio` |
> | **kvm4** | `otaviomiranda.cloud` | `191.101.70.130` | `10.100.0.4/24` | `luizotavio` |
> | **kvm8** | `myswarm.cloud` | `89.116.73.152` | `10.100.0.8/24` | `luizotavio` |

> **Dica Hostinger (Alternativa):**
> Você também pode configurar o Hostname diretamente pelo hPanel em **VPS > Configurações > Configurações de VPS**. O painel valida se o domínio realmente pertence a você (ou aponta para a VPS). Se validado, ele configura o hostname automaticamente dentro do sistema operacional, dispensando o comando `hostnamectl`.

*Repita o processo para `kvm4` e `kvm8` ajustando os nomes e domínios adequados.*

## 3. Firewall de Borda (hPanel)

Antes de configurar o firewall interno (UFW), configuramos o **Firewall da Hostinger** (hPanel) para proteger a rede antes mesmo que o tráfego chegue nas VPSs.

A política adotada é **Whitelist**: Bloqueia tudo (Drop) e libera apenas o necessário.

**Regras Aplicadas (Aplicar em TODAS as VPS):**

| Ação | Protocolo | Porta | Origem (Source) | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| **Accept** | TCP | Any | `187.108.118.25` (Seu IP) | Acesso total do admin (SSH, etc) |
| **Accept** | TCP | Any | `89.116...`, `191.101...`, `76.13...` | Comunicação total entre os nós (Swarm TCP) |
| **Accept** | UDP | `4789` | `89.116...`, `191.101...`, `76.13...` | Swarm Overlay Network (VXLAN) |
| **Accept** | UDP | `7946` | `89.116...`, `191.101...`, `76.13...` | Swarm Container Network Discovery |
| **Accept** | ICMP | Any | `89.116...`, `191.101...`, `76.13...` | Ping entre os nós |
| **Accept** | ICMP | Any | `187.108.118.25` (Seu IP) | Ping do admin |
| **Accept** | HTTPS | `443` | `Any` (Qualquer) | Tráfego Web Seguro (Traefik) |
| **Accept** | HTTP | `80` | `Any` (Qualquer) | Tráfego Web (Traefik) |
| **Accept** | UDP | `51820` | IPs dos Nós + Seu IP | WireGuard VPN |
| **Accept** | TCP | `8080` | `187.108.118.25` (Seu IP) | Traefik Dashboard (Dev/Debug) |
| **Drop** | Any | Any | `Any` | **Regra Final: Bloqueia todo o resto** |

> **Nota:** Certifique-se de substituir o IP `187.108.118.25` pelo **SEU IP** atual de internet. Os demais IPs devem ser os IPs das suas outras VPSs.

> **Importante:** Essa configuração protege a borda. Ainda assim, configuraremos o `UFW` (firewall local) mais adiante para defesa em profundidade e controle da VPN.

## 4. Criação do Usuário e Docker

Ainda logado como `root` (via Terminal web ou SSH), vamos criar o usuário de trabalho e garantir que ele tenha acesso ao Docker e poderes administrativos.

**Execute em TODAS as VPSs (`kvm2`, `kvm4`, `kvm8`):**

```bash
# Defina o nome do seu usuário
export YOUR_USERNAME="luizotavio"

# Cria o usuário com diretório home (-m) e shell bash (-s)
useradd -m -s /bin/bash $YOUR_USERNAME

# Adiciona ao grupo 'sudo' (admin) e 'docker' (para rodar docker sem sudo)
usermod -aG sudo $YOUR_USERNAME
usermod -aG docker $YOUR_USERNAME

# Define a senha do usuário
passwd $YOUR_USERNAME

# Teste o acesso mudando para o novo usuário
su $YOUR_USERNAME
```

> **Verificação:** Após rodar `su $YOUR_USERNAME`, tente rodar `docker ps`. Se funcionar sem erro de permissão, o grupo `docker` foi aplicado corretamente. Se pedir senha no `sudo`, está correto.

## 5. Configuração SSH (Chaves e Acesso Fácil)

Agora vamos configurar o acesso seguro e prático a partir do **SEU COMPUTADOR**. Isso elimina a necessidade de digitar senhas e IPs o tempo todo.

**1. Gerar par de chaves SSH (no seu PC):**
Se você ainda não tem uma chave específica para este projeto:
```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_hostinger -C "luizotavio"
```

**2. Enviar a chave pública para as VPSs:**
Isso autoriza sua chave a entrar nos servidores. Repita para cada IP ou domínio configurado.
```bash
ssh-copy-id -i ~/.ssh/id_hostinger.pub luizotavio@inprod.cloud
ssh-copy-id -i ~/.ssh/id_hostinger.pub luizotavio@otaviomiranda.cloud
ssh-copy-id -i ~/.ssh/id_hostinger.pub luizotavio@myswarm.cloud
```

**3. Criar "apelidos" no `~/.ssh/config` (no seu PC):**
Para não precisar digitar `ssh luizotavio@inprod.cloud` toda hora, vamos criar atalhos (`ssh kvm2`).

Edite ou crie o arquivo `~/.ssh/config`:
```text
Host kvm2
  IgnoreUnknown AddKeysToAgent,UseKeychain
  AddKeysToAgent yes
  HostName inprod.cloud
  User luizotavio
  Port 22
  IdentityFile ~/.ssh/id_hostinger

Host kvm4
  IgnoreUnknown AddKeysToAgent,UseKeychain
  AddKeysToAgent yes
  HostName otaviomiranda.cloud
  User luizotavio
  Port 22
  IdentityFile ~/.ssh/id_hostinger

Host kvm8
  IgnoreUnknown AddKeysToAgent,UseKeychain
  AddKeysToAgent yes
  HostName myswarm.cloud
  User luizotavio
  Port 22
  IdentityFile ~/.ssh/id_hostinger
```

**Teste:**
Agora basta digitar:
```bash
ssh kvm2
```
Se conectar direto, está tudo pronto!

## 6. Sudo sem Senha (Opcional/Demo)

Para agilizar o desenvolvimento e evitar digitar a senha de `sudo` repetidamente durante o vídeo/configuração, vamos configurar o `NOPASSWD`.

> **⚠️ ALERTA DE SEGURANÇA:**
> Em ambientes de produção críticos, isso **não é recomendado**. Se um atacante ganhar acesso ao seu usuário, ele ganha acesso `root` instantaneamente sem barreiras. Faça isso apenas se entender o risco ou para ambientes de laboratório/demo.

**Em cada VPS:**

```bash
# Cria/edita um arquivo específico para seu usuário no sudoers.d
sudo visudo -f /etc/sudoers.d/luizotavio
```

Adicione a linha abaixo (trocando `luizotavio` pelo seu usuário):

```text
luizotavio ALL=(ALL) NOPASSWD: ALL
```

Salve e saia. Agora comandos como `sudo apt update` rodarão direto.

## 7. Atualização e Pacotes Básicos

Vamos garantir que o sistema esteja seguro, atualizado e com nossas ferramentas favoritas instaladas.

**Execute em TODAS as VPSs:**

```bash
# Define seu fuso horário (ajuste conforme necessário)
export TIMEZONE='America/Sao_Paulo'

# Atualiza repositórios e pacotes do sistema
sudo apt update -y
sudo apt upgrade -y

# Instala ferramentas essenciais
# just: task runner (usaremos muito)
# python3/build-essential: para scripts e compilação
# acl: para controle fino de permissões
sudo apt install -y vim curl ca-certificates htop python3 \
python3-dev acl build-essential tree just

# Aplica o fuso horário
sudo timedatectl set-timezone "$TIMEZONE"
```

## 8. Configuração do Git

Como vamos clonar o repositório e talvez fazer ajustes rápidos, configuramos o Git com nossa identidade.

**Execute em TODAS as VPSs:**

```bash
# Ajuste com seus dados
export GIT_USERNAME="luizomf"
export GIT_EMAIL="luizomf@gmail.com"

git config --global user.name "$GIT_USERNAME"
git config --global user.email "$GIT_EMAIL"

# Padronização de quebra de linha (Linux style - LF)
git config --global core.autocrlf input
git config --global core.eol lf

# Branch padrão moderna
git config --global init.defaultbranch main
```

## 9. Hardening do SSH (Blindando o Acesso)

Agora vamos trancar as portas. Desabilitaremos login por senha e acesso de root, deixando apenas nossas chaves autorizadas.

> **⚠️ ALERTA CRÍTICO (Tranqueira à vista):**
> Este passo **DESATIVA** o login por senha.
> 1. Certifique-se que você já configurou suas chaves SSH (`ssh-copy-id`) no passo anterior e testou o acesso (`ssh kvm2`).
> 2. Se você rodar isso sem ter a chave configurada, **VOCÊ PERDERÁ O ACESSO SSH** e terá que usar o console de emergência da Hostinger para consertar.

**Execute em TODAS as VPSs:**

```bash
# Instala o servidor SSH (geralmente já vem, mas garante)
sudo apt install -y openssh-server

# Cria nosso arquivo de configuração blindada
cat <<-'EOF' | sudo tee "/etc/ssh/sshd_config.d/01_sshd_settings.conf"
###############################################################################
### Start of /etc/ssh/sshd_config.d/01_sshd_settings.conf ######################
###############################################################################

# BLOCK 1: AUTHENTICATION AND ACCESS
PubkeyAuthentication yes            # Apenas chaves
PasswordAuthentication no           # Senhas desativadas (adeus brute-force)
KbdInteractiveAuthentication no     # Sem teclado interativo
ChallengeResponseAuthentication no  # Sem desafio-resposta
PermitRootLogin no                  # Root nunca loga direto
PermitEmptyPasswords no             # Sem senhas vazias
UsePAM yes                          # PAM ativo para sessão (mas auth é só key)
AuthenticationMethods publickey     # Força auth apenas por chave pública

# BLOCK 2: ATTACK SURFACE REDUCTION
PermitUserEnvironment no            # Bloqueia injeção de env
PermitUserRC no                     # Bloqueia scripts rc de usuário
X11Forwarding no                    # Sem interface gráfica remota

# TUNNELING (Ajuste se precisar de túneis)
AllowTcpForwarding no               # Bloqueia túneis TCP
AllowStreamLocalForwarding no       # Bloqueia socket forwarding
AllowAgentForwarding no             # Bloqueia agent forwarding

PermitOpen none                     # Bloqueia forwarding arbitrário
PermitListen none                   # Bloqueia abrir portas remotas
GatewayPorts no                     # Bloqueia gateway ports
PermitTunnel no                     # Bloqueia interfaces tun/tap

# BLOCK 3: PERFORMANCE & TIMEOUTS
MaxAuthTries 4                      # Max 4 tentativas
LoginGraceTime 30                   # 30s para logar ou tchau
ClientAliveInterval 300             # Keepalive a cada 5 min
ClientAliveCountMax 2               # Cai se não responder 2x
PrintMotd no                        # Menos spam no login
UseDNS no                           # Login rápido (sem reverse DNS lookup)

###############################################################################
### End of /etc/ssh/sshd_config.d/01_sshd_settings.conf ########################
###############################################################################
EOF

# Testa a configuração antes de reiniciar (se der erro, NÃO reinicie)
sudo sshd -t

# Reinicia o serviço SSH para aplicar
sudo systemctl restart ssh
```

> **Dica:** Mantenha sua sessão atual aberta. Abra **outro terminal** no seu PC e tente conectar (`ssh kvm2`). Se funcionar, sucesso! Se não, você ainda tem a sessão aberta para corrigir.

## 10. Fail2Ban (Proteção Brute-Force)

Mesmo sem senhas, logs de tentativas de acesso poluem o sistema e consomem recursos. O Fail2Ban bloqueia IPs que tentam conectar e falham repetidamente.

**Execute em TODAS as VPSs:**

```bash
# Defina o IP da sua casa/escritório para nunca ser banido (whitelist)
export ADMIN_SSH_CIDR="187.108.118.25/32" # <-- Troque pelo SEU IP
export FAIL2BAN_IGNOREIP="$ADMIN_SSH_CIDR 127.0.0.1/8 ::1"

# Instala o Fail2Ban
sudo apt install fail2ban -y

# Cria a configuração local (jail.local)
cat <<-EOF | sudo tee "/etc/fail2ban/jail.local"
[DEFAULT]

[sshd]
enabled = true
port = ssh
backend = systemd
# IPs ignorados (você e o localhost)
ignoreip = ${FAIL2BAN_IGNOREIP}

# Regras de banimento
maxretry = 5          # 5 tentativas falhas
findtime = 10m        # dentro de 10 minutos
bantime = 1h          # = Banido por 1 hora

# Banimento progressivo para reincidentes
bantime.increment = true
bantime.factor = 2    # Dobra o tempo a cada reincidência
bantime.max = 24h     # Até o máximo de 24h
EOF

# Reinicia o serviço
sudo systemctl restart fail2ban
```

## 11. Firewall Local (UFW)

Defesa em profundidade. Se o firewall da Hostinger falhar ou for desativado, o UFW garante que ninguém acessa o que não deve.

Aqui fazemos algo especial: **Liberamos o Swarm APENAS na interface VPN (`wg0`)**. Se alguém bater no IP público tentando falar com o Docker Swarm, será bloqueado.

**Execute em TODAS as VPSs:**

```bash
# Defina seu IP e a rede da VPN
export ADMIN_SSH_CIDR="187.108.118.25/32"    # <-- Troque pelo SEU IP
export WG_CIDR="10.100.0.0/24"              # Rede interna que usaremos no WireGuard
export WG_INTERFACE="wg0"                   # Interface do WireGuard

sudo apt install -y ufw

# Zera configurações antigas (garante estado limpo)
sudo ufw disable
sudo ufw --force reset

# Política Padrão: Bloqueia tudo que entra, Libera tudo que sai
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Libera SEU acesso SSH e WireGuard (UDP)
sudo ufw allow from "$ADMIN_SSH_CIDR" to any port 22 proto tcp comment "SSH Admin"
sudo ufw allow from "$ADMIN_SSH_CIDR" to any port 51820 proto udp comment "WireGuard Admin"

# Libera tráfego do SWARM e NFS APENAS na interface da VPN (wg0)
# Ninguém de fora da VPN consegue tocar nesses serviços
sudo ufw allow in on "$WG_INTERFACE" from "$WG_CIDR" to any port 2377 proto tcp comment "Swarm control (wg)"
sudo ufw allow in on "$WG_INTERFACE" from "$WG_CIDR" to any port 7946 proto tcp comment "Swarm gossip (wg)"
sudo ufw allow in on "$WG_INTERFACE" from "$WG_CIDR" to any port 7946 proto udp comment "Swarm gossip (wg)"
sudo ufw allow in on "$WG_INTERFACE" from "$WG_CIDR" to any port 4789 proto udp comment "Swarm vxlan (wg)"
sudo ufw allow in on "$WG_INTERFACE" from "$WG_CIDR" to any port 2049 proto tcp comment "NFSv4 (wg)"
```

**Execute APENAS no nó `kvm8` (Edge/Traefik):**

```bash
# O kvm8 é o único que recebe tráfego web público
sudo ufw allow 80/tcp comment "HTTP public"
sudo ufw allow 443/tcp comment "HTTPS public"
```

**Finalizar e Ativar (EM TODAS):**

```bash
# Se você errou o IP do SSH lá em cima, você vai cair agora.
sudo ufw --force enable
sudo ufw status verbose
```










