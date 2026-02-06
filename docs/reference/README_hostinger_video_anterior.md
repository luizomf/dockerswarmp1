# Guia para o desenvolvedor

> **Referencia:** este arquivo vem de um video anterior (single VPS). Serve como
> material extra e como base de texto, mas nao e necessario para este projeto
> do Swarm em 3 VPS.

> **NOTA:** solicitei ao Gemini para fazer uma explicação mais detalhada em cada
> comando que usei. Espero que ajude ainda mais. Além disso, este projeto conta
> com um arquivo `AGENTS.md` detalhando tudo. Isso permite que você use o
> projeto com outros agentes de sua preferência. Se precisar, leia-o e ajuste-o.

Use este guia para aplicar os comandos passo a passo no seu próprio servidor.
Estou usando o [KVM 2 da Hostinger](https://hostinger.com/otaviomiranda), mas
isso deve funcionar em qualquer servidor.

Também detalhei este processo em vídeo caso queira assistir:

[![YouTube Video](http://img.youtube.com/vi/yxxEk68EDgo/hqdefault.jpg)](https://youtu.be/yxxEk68EDgo 'Crie seu próprio cloud em VPS')

- Link: [https://youtu.be/yxxEk68EDgo](https://youtu.be/yxxEk68EDgo)

---

## Onde contratar um servidor?

Se você busca um servidor **robusto, confiável e com preço imbatível**,
recomendo o [KVM 2 da Hostinger](https://hostinger.com/otaviomiranda). Você pode
escolher outros KVMs maiores ou menores conforme a necessidade. No entanto, o
custo benefício do KVM 2 é o melhor (você vai perceber isso por conta própria).

**Bônus Exclusivo:** Consegui **10% de desconto adicional** para vocês. Basta
usar o cupom abaixo no carrinho:

- Cupom: `OTAVIOMIRANDA`

---

## Personalização dos valores

Use seu editor para substituir as chaves à esquerda no bloco de texto abaixo
para os seus dados. Estes são os "apelidos" que usaremos ao longo do guia para
representar suas informações.

```text
SEU_NOME - Seu nome (Ex.: João da Silva)
SEU_USUARIO_SERVER - Seu nome de usuário para o servidor (Ex.: joaosilva)
SEU_EMAIL - Seu e-mail para o certbot (Ex.: joaosilva@email.com)
IP_SERVER - IP do seu VPS (Ex.: 191.27.48.56)
DOMINIO_SERVER - Seu domínio atrelado ao IP do server (Ex.: exemplo.com)
SEU_USUARIO_GITHUB - Seu usuário do GitHub (Ex.: joaozinho)
URL_REPOSITORIO - A URL SSH do seu GitHub (Ex.: git@github.com:user/repo.git)
```

---

## Local

Caso ainda não tenho feito isso, copie o arquivo `.env.example` para `.env` e
modifique os valores como preferir.

Sempre que for desenvolver em ambiente local (seu computador), mantenha a
variável de ambiente `CURRENT_ENV` como `development` no arquivo `.env`. Deixei
instruções no arquivo também.

---

## Como fazer `build` das imagens localmente

Existe um arquivo chamado
[./compose.override.example](compose.override.example). Basta copiá-lo para
`compose.override.yaml`. As configurações feitas no `compose.yaml` são de
produção, já a configurações feitas no `compose.override.yaml` são de
desenvolvimento.

Não é necessário reescrever todo o `compose.override.yaml`, apenas coisas que
você quer sobrescrever. Por exemplo, se estamos fazendo `build` local, não
queremos baixar as imagens do repositório (elas pode nem existir ainda).

---

## Na Hostinger

### Instalação ou reinstalação do sistema operacional

Vou usar o **Ubuntu 24.04 with Docker** da Hostinger. Se quiser seguir
exatamente como estou fazendo, abaixo estão os passos para instalar ou
reinstalar o sistema operacional.

> **Atenção:** reinstalar um sistema operacional novo no servidor significa que
> todos os dados serão apagados do disco. Certifique-se de fazer backup caso
> tenha salvo dados importantes nele.

No menu `VPS` > `SO e Painel` > `Mudar SO` > `SO com Aplicativo`, acesse o campo
de pesquisa e digite `Docker`. Você verá um aplicativo com a logo e nome do
Docker.

Clique neste ícone e depois na opção "Alterar sistema operacional". Como vamos
apagar tudo para instalar um novo sistema operacional, leia atentamente a
mensagem e confirme.

Configure uma senha forte, que você vá se lembrar depois, para o usuário `root`
do seu novo servidor e confirme.

Agora é só aguardar.

---

### Chaves SSH

Por segurança, vamos desativar o acesso por senha e permitir apenas acesso via
SSH.

Para criar seu par de chaves pública e privada use o comando abaixo:

```sh
# NO SEU COMPUTADOR
# Este comando cria um par de chaves SSH usando o algoritmo Ed25519.
# Por que Ed25519? É um algoritmo moderno, mais rápido e considerado mais
# seguro que os tradicionais RSA.
# O -f define o nome do arquivo, para não sobrescrever sua chave padrão.
# O -C é um comentário, geralmente seu e-mail ou user@host.
ssh-keygen -t ed25519 -f ~/.ssh/id_hostinger -C "${USER}"
```

Nas configurações do seu VPS, acesse `Chaves SSH` > `Adicionar chave SSH`. Copie
o valor do arquivo `~/.ssh/id_hostinger.pub` e cole no campo
`Conteúdo da chave SSH`. Tenha certeza de usar a chave pública (`.pub`), nunca a
chave privada.

```sh
# NO SEU COMPUTADOR
# O comando 'cat' simplesmente exibe o conteúdo do arquivo.
# Copie a saída deste comando.
cat ~/.ssh/id_hostinger.pub
```

No Painel da Hostinger, vá em `VPS` > Escolha o VPS e `Gerenciar` >
`Configurações` > `Chaves SSH`. Crie uma chave SSH e cole o valor que você
copiou acima.

Essa chave permite que o usuário `root` acesse o servidor sem senha (vamos
desativar isso depois).

Vamos fazer o primeiro acesso ao servidor, então use este comando no seu
terminal:

```sh
# NO SEU COMPUTADOR
# Estamos nos conectando como 'root' pela primeira vez para configurar o servidor.
# O -i especifica o arquivo de identidade (nossa chave privada) a ser usado.
ssh root@DOMINIO_SERVER -i ~/.ssh/id_hostinger
# Ou
ssh root@IP_SERVER -i ~/.ssh/id_hostinger
```

---

## No servidor ou seu computador local

### Atualização e pacotes básicos no servidor

Vamos atualizar tudo e instalar alguns pacotes úteis para o servidor.

```sh
# NO SERVIDOR (Usuário root)
# Por que fazer isso primeiro? Servidores recém-criados vêm com uma "foto"
# do sistema daquele momento. Fazer o update e upgrade garante que todos
# os pacotes e o próprio sistema operacional recebam as últimas atualizações
# de segurança e correções de bugs. É o primeiro passo para ter um sistema seguro.
apt update
apt upgrade -y

apt install -y vim curl ca-certificates htop python3 \
python3-dev acl build-essential tree just

# Ajusta o fuso horário do servidor. É importante para que os logs,
# agendamentos (cron jobs) e a própria aplicação tenham um horário consistente.
# Lista: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
sudo timedatectl set-timezone America/Sao_Paulo
```

---

### Seu usuário no servidor

Configuramos nosso usuário. Troque `SEU_USUARIO_SERVER` para o nome que deseja
para seu usuário.

```sh
# NO SERVIDOR (Usuário root)
# Por que criar um usuário? É uma das práticas de segurança mais importantes,
# chamada "Princípio do Menor Privilégio". O usuário 'root' tem poder
# ilimitado, o que é perigoso. Criamos um usuário separado para o dia a dia,
# que só usará poderes administrativos ('sudo') quando for realmente necessário.
useradd SEU_USUARIO_SERVER -m -s /bin/bash
```

Defina a senha para seu usuário.

```sh
# NO SERVIDOR (Usuário root)
passwd SEU_USUARIO_SERVER
```

Você não precisa fazer isso se não quiser, mas eu gosto de usar o editor vim no
servidor. Se você não tem experiência com isso, troque a palavra `vim` para
`nano`.

```sh
# NO SERVIDOR (Usuário root)
# Escolha o número do editor de sua preferência, eu vou usar o vim
# a outra opção popular é nano. (Mais fácil de usar).
update-alternatives --config editor

# ISSO É OPCIONAL E TENHA CUIDADO (Só use se souber o que está fazendo)
# Isso configura o vim como editor e muda o seu terminal para vi-mode.
# Se não entendeu os comentários acima, pule esses dois comandos abaixo.
curl https://gist.githubusercontent.com/luizomf/9a52ba5b7b43aa69cc9a7121795bb9fa/raw/34d7d9b60e0a0d655cbb2cba8f8d0de8d0238dda/bash_minimal_setup >> ~/.bashrc
curl https://gist.githubusercontent.com/luizomf/9a52ba5b7b43aa69cc9a7121795bb9fa/raw/8db0fd8032a412c95fe7f127b939317dc0f38c0e/.vimrc > ~/.vimrc
source ~/.bashrc
```

Nosso usuário precisa de acesso ao `sudo` para tarefas administrativas. Você tem
duas opções: usar o `sudoers` ou adicionar seu usuário no grupo `sudo`. Vou
adicionar meu usuário no grupo `sudo` (isso só fará efeito depois que você logar
novamente).

```sh
# NO SERVIDOR
# Por que adicionar ao grupo 'sudo'? Isso permite que nosso usuário execute
# comandos como se fosse o 'root' usando o prefixo 'sudo'. É a maneira
# controlada de realizar tarefas administrativas sem estar logado como 'root'.
usermod -aG sudo SEU_USUARIO_SERVER

# Como o servidor já tem o docker instalado, podemos
# adicionar nosso usuário no grupo do docker.
# Por que? Para que nosso usuário possa executar comandos 'docker'
# sem precisar usar 'sudo' toda vez. Facilita o gerenciamento dos contêineres.
sudo usermod -aG docker SEU_USUARIO_SERVER
```

Faça login com seu usuário.

```sh
# NO SERVIDOR (Usuário root)
# Isso loga com seu usuário
su SEU_USUARIO_SERVER
# Isso vai para a home do seu usuário
cd ~
```

Agora pegamos a chave SSH que jogamos no `root` anteriormente e passamos ela
para nosso usuário.

```sh
# NO SEU COMPUTADOR
# O comando 'ssh-copy-id' é a forma mais fácil e segura de instalar uma chave
# pública em um servidor remoto. Ele cuida de criar o arquivo
# `~/.ssh/authorized_keys` e ajustar as permissões corretamente.
ssh-copy-id -i ~/.ssh/id_hostinger.pub SEU_USUARIO_SERVER@DOMINIO_SERVER

# Faça o teste e veja se loga com seu usuário sem senha.
ssh SEU_USUARIO_SERVER@DOMINIO_SERVER -i ~/.ssh/id_hostinger
# ENTROU? Ok, volte para seu terminal normal (seu computador)
exit
```

Para não ter que ficar digitando a chave, usuário e senha, vamos configurar
`~/.ssh/config`.

```sh
# NO SEU COMPUTADOR
# Por que fazer isso? Este arquivo é um atalho. Ele permite que você crie
# "apelidos" para suas conexões SSH. Em vez de digitar o comando longo toda vez,
# você poderá simplesmente digitar 'ssh hostinger'.
vim ~/.ssh/config

###############################################################################
### Início do ~/.ssh/config ###################################################
###############################################################################

# ... Podem existir outros blocos aqui ...

# Cole o bloco abaixo substituindo os valores indicados
Host hostinger
  IgnoreUnknown AddKeysToAgent,UseKeychain
  AddKeysToAgent yes
  HostName DOMINIO_SERVER
  User SEU_USUARIO_SERVER
  Port 22
  IdentityFile ~/.ssh/id_hostinger

# ... Podem existir outros blocos aqui ...

###############################################################################
### Fim do ~/.ssh/config ######################################################
###############################################################################

# Agora o comando é apenas
ssh hostinger
```

Agora você pode remover aquela chave SSH do painel se quiser, não vamos mais
precisar dela.

OPCIONAL - Nós já fizemos isso para o `root`, agora vou fazer o mesmo para meu
usuário. Configurar o `vim` e `vi-mode`. Pode pular esse bloco tranquilamente.

```sh
# NO SERVIDOR (Seu usuário)
# ISSO É OPCIONAL E TENHA CUIDADO (Só use se souber o que está fazendo)
# Isso configura o vim como editor e muda o seu terminal para vi-mode.
# Se não entendeu os comentários acima, pule esses dois comandos abaixo.
curl https://gist.githubusercontent.com/luizomf/9a52ba5b7b43aa69cc9a7121795bb9fa/raw/34d7d9b60e0a0d655cbb2cba8f8d0de8d0238dda/bash_minimal_setup >> ~/.bashrc
curl https://gist.githubusercontent.com/luizomf/9a52ba5b7b43aa69cc9a7121795bb9fa/raw/8db0fd8032a412c95fe7f127b939317dc0f38c0e/.vimrc > ~/.vimrc
source ~/.bashrc
```

---

### Reforçando a segurança para o SSH no servidor

**Observação**: as descrições foram escritas foi vários LLMs diferentes. Essa
última verificação e descrição foi feita pelo Codex (GPT 5.2).

```sh
# NO SERVIDOR (Seu usuário)
# Por que criar um novo arquivo em 'sshd_config.d'? Isso mantém nossas
# customizações separadas do arquivo de configuração principal (/etc/ssh/sshd_config).
# Se uma atualização do sistema modificar o arquivo principal, nossas regras
# permanecem intactas. É uma forma organizada e segura de gerenciar configurações.
sudo vim /etc/ssh/sshd_config.d/01_sshd_settings.conf

###############################################################################
### Início do /etc/ssh/sshd_config.d/01_sshd_settings.conf ####################
###############################################################################

# BLOCO 1: AUTENTICAÇÃO E ACESSO (HARDENING)
# Foco: Eliminar métodos inseguros e garantir que apenas chaves entrem.

PubkeyAuthentication yes           # Habilita autenticação por chaves públicas
PasswordAuthentication no          # Desabilita senhas (imune a brute force)
KbdInteractiveAuthentication no    # Desabilita login interativo por teclado
ChallengeResponseAuthentication no # Desabilita desafios genéricos de resposta
PermitRootLogin no                 # Proíbe login do root (regra de ouro)
PermitEmptyPasswords no            # Proíbe senhas vazias
UsePAM no                          # Desativa o PAM (reduz superfície de ataque)
AuthenticationMethods publickey    # Força o uso exclusivo de chaves públicas

# BLOCO 2: REDUÇÃO DA SUPERFÍCIE DE ATAQUE (CONECTIVIDADE)
# Foco: Desativar túneis e funções de rede que podem ser usadas para pivoteamento.

PermitUserEnvironment no           # Impede injeção de variáveis via ~/.ssh/environment
PermitUserRC no                    # Desativa execução de scripts ~/.ssh/rc no login
X11Forwarding no                   # Desabilita interface gráfica remota

# TÚNEIS E ENCAMINHAMENTO
# ATENÇÃO: Se usar SOCKS Proxy (-D) ou túneis TCP, mude para 'yes'.
AllowTcpForwarding no

# ATENÇÃO: Se usar 'Docker Context' via SSH, mude para 'yes'.
# Em 'no', o Docker CLI não acessa o docker.sock remoto.
AllowStreamLocalForwarding no

# ATENÇÃO: Se for usar o Agent Forwarding para pular entre máquinas, mude para 'yes'.
AllowAgentForwarding no

PermitOpen none                    # Bloqueia redirecionamento para destinos (L4)
PermitListen none                  # Impede o servidor de abrir portas remotas
GatewayPorts no                    # Bloqueia acesso externo a túneis reversos
PermitTunnel no                    # Desativa criação de adaptadores virtuais (tun/tap)

# BLOCO 3: AJUSTES FINOS E QUALIDADE DE VIDA
# Foco: Controle de sessão e performance.

MaxAuthTries 4                     # Máximo de tentativas de login por conexão
LoginGraceTime 30                  # Tempo limite para completar o login (segundos)
ClientAliveInterval 300            # Verifica se o cliente está ativo a cada 5 min
ClientAliveCountMax 2              # Desconecta após 2 verificações sem resposta
PrintMotd no                       # Evita duplicidade na mensagem do dia
UseDNS no                          # Desativa DNS reverso (login muito mais rápido)

###############################################################################
### Fim do /etc/ssh/sshd_config.d/01_sshd_settings.conf #######################
###############################################################################

# Reinicie o serviço SSH para que as novas configurações sejam aplicadas.
sudo systemctl restart ssh

# NÃO FECHE ESTA CONEXÃO AINDA.
# Por que? Se você cometeu um erro no arquivo de configuração, o serviço SSH
# pode não iniciar, e você ficará trancado para fora do servidor.
# Abra OUTRA aba do terminal e teste a conexão.
ssh hostinger

# Se a nova conexão funcionar, significa que suas regras estão corretas.
# Agora é seguro fechar a conexão antiga. Podemos até reiniciar o servidor
# para garantir que tudo sobe corretamente no boot.
sudo reboot
```

---

### Configure o git para seu usuário no servidor

Configure o git para evitar erros bobos no futuro.

```sh
# NO SERVIDOR (Seu usuário, não usaremos mais o root)
# Por que fazer isso? Essas configurações são usadas para identificar quem fez
# cada alteração (commit). Além disso, a configuração de 'autocrlf' e 'eol'
# padroniza as terminações de linha (LF para Linux/Mac), evitando problemas
# de formatação de arquivos entre diferentes sistemas operacionais.
git config --global user.name "SEU_USUARIO_GITHUB"
git config --global user.email "SEU_EMAIL"
git config --global core.autocrlf input
git config --global core.eol lf
git config --global init.defaultbranch main
```

---

### O diretório do projeto no servidor

```sh
# NO SERVIDOR
# Criamos um diretório na raiz do sistema para nosso projeto.
sudo mkdir /dockerlabs
# Definimos nosso usuário e grupo como donos do diretório.
sudo chown -R SEU_USUARIO_SERVER:SEU_USUARIO_SERVER /dockerlabs
# Permissões 775: Dono (rwx), Grupo (rwx), Outros (r-x).
sudo chmod -R 775 /dockerlabs

# Por que isso? 'git' por padrão se recusa a operar em diretórios que não
# pertencem ao usuário atual, como medida de segurança. Estamos dizendo ao git
# que '/dockerlabs' é um diretório seguro para operações.
git config --global --add safe.directory /dockerlabs

# --- A Mágica das Permissões para Deploy ---
# O que estamos fazendo aqui é crucial para o deploy automático funcionar.
# O objetivo é garantir que qualquer arquivo ou diretório criado dentro de
# /dockerlabs, seja pelo nosso usuário ou por um processo do sistema
# (como o script de deploy), sempre tenha as permissões corretas.

# 'setfacl' (Set File Access Control Lists) define regras de permissão padrão.
# 'd:g:SEU_USUARIO_SERVER:rwx' significa que, por padrão (d), qualquer novo
# item criado aqui dará ao grupo (g) 'SEU_USUARIO_SERVER' permissões de
# leitura, escrita e execução (rwx).
sudo setfacl -R -m d:g:SEU_USUARIO_SERVER:rwx /dockerlabs
sudo chmod -R 775 /dockerlabs
# 'chmod g+s' (setgid bit): Faz com que novos arquivos/pastas criados
# dentro de /dockerlabs herdem o grupo do diretório pai (SEU_USUARIO_SERVER),
# em vez do grupo primário de quem os criou. Isso evita o clássico problema
# de "permissão negada" durante o deploy.
sudo chmod g+s /dockerlabs
```

---

### Fail2Ban jails - Ainda mais segurança no servidor

O Fail2Ban vai reforçar ainda mais a segurança do nosso SSH. Ele lê logs de
tentativa de login inválidas (geralmente vindas de bots) e bloqueia estes IPs
por um determinado tempo.

- [Fail2Ban - Daemon to ban hosts that cause multiple authentication errors](https://github.com/fail2ban/fail2ban)

```sh
# NO SERVIDOR
# Instalar o Fail2Ban
sudo apt install fail2ban

# Vamos criar um arquivo de "jail" local.
# Por que '.local'? As configurações padrão estão em 'jail.conf'. Nunca
# editamos esse arquivo diretamente, pois ele pode ser sobrescrito por
# atualizações. O 'jail.local' é nosso, e suas regras têm prioridade.
sudo vim /etc/fail2ban/jail.local

# Só copiar e colar o trecho abaixo

###############################################################################
### INICIO DO /etc/fail2ban/jail.local ########################################
###############################################################################

[DEFAULT]
# Por que 'ignoreip'? Para garantir que você não se bloqueie acidentalmente.
# Adicione aqui seu IP fixo ou o da sua rede, se souber.
ignoreip = 127.0.0.1/8 ::1
allowipv6 = auto

[sshd]
# Esta é a "jaula" específica para o serviço SSH.
enabled  = true
port     = ssh
# Usa o 'systemd' para encontrar os logs, que é o padrão moderno.
backend  = systemd

# Tolera 5 erros em 10 minutos antes de banir.
maxretry = 5
findtime = 10m
# O banimento inicial dura 1 hora.
bantime  = 1h

# Por que 'increment'? Para punir agressores persistentes com mais severidade.
# Se um mesmo IP for banido várias vezes, o tempo de banimento aumenta.
bantime.increment = true
# O tempo de ban aumenta em um fator de 2 a cada novo ban (1h -> 2h -> 4h...).
bantime.factor    = 2
# O banimento máximo que pode ser aplicado é de 24 horas.
bantime.max       = 24h

###############################################################################
### FIM DO /etc/fail2ban/jail.local ###########################################
###############################################################################

# Salve o arquivo e reinicie o serviço para aplicar a nova configuração.
sudo systemctl restart fail2ban
```

---

#### 🚨 FUI BLOQUEADO - SERVIDOR PAROU DE RESPONDER

Estou adicionando esse trecho aqui justamente por ter acontecido comigo. Estava
testando configurações e o servidor parou de responder inesperadamente. Você vai
pensar em todos os motivos possíveis para o problema: sua Internet, a Hostinger,
seu servidor, seu domínio, etc. Mas, na grande maioria das vezes é o Fail2Ban.

Se você errar a senha mais de 5 vezes, será bloqueado (isso porque aumentei,
estava 1x apenas). Ele libera automaticamente após 1 hora.

Claro que você não precisa esperar uma hora. Vá no seu painel da Hostinger
(hpanel), **VPS**, **Gerenciar**. Bem no topo existe um botão `Terminal`. Clique
nele e faça login com o `root` (se não lembrar a senha, vá em "Configurações" e
altere).

![Terminal no hpanel](./assets/images/hpanel_terminal.png)

Devidamente logado, pare o serviço do Fail2Ban e teste para ver se volta a logar
do seu computador local.

```sh
# 🚨 Só pare o serviço se for necessário, do contrário nem toque nisso
# Sem sudo porque já estamos como root, do contrário use:
# sudo systemctl stop fail2ban
systemctl stop fail2ban

# 🚨 Sempre que parar o serviço por algum motivo, inicie novamente depois que terminar:
sudo systemctl start fail2ban
```

Se voltar era ele mesmo. Deixo um pequeno guia para que você gerencie os IPs
banidos pelo Fail2Ban. Mas, considere usar apenas chaves SSH. Login por senha é
menos seguro e está vulnerável a ataques de brute force. Além disso, considere
adicionar o seu IP ou a rede do seu provedor (se possível) em `ignoreip`.

---

#### Manual básico do Fail2Ban para o dia a dia (Cheat Sheet)

```sh
# VERIFICAR STATUS

# Ver o status geral (quais jails estão ativas)
sudo fail2ban-client status

# Ver estatísticas do SSH (quantos banidos, lista de IPs, etc.)
# Nota: 'sshd' é o nome da jail definida no arquivo .local
sudo fail2ban-client status sshd

# "DESBANIR" (UNBAN)
# Caso você ou um colega tenha sido bloqueado sem querer.

# Sintaxe: fail2ban-client set <NOME_DA_JAIL> unbanip <IP>
sudo fail2ban-client set sshd unbanip 192.168.1.50

# Dica: Se quiser "desbanir" todo mundo (limpar a lista)
sudo fail2ban-client unban --all

# BANIR MANUALMENTE
# Viu um IP suspeito nos logs e quer bloquear agora?

# Sintaxe: fail2ban-client set <NOME_DA_JAIL> banip <IP>
sudo fail2ban-client set sshd banip 203.0.113.45

# MONITORAMENTO (LOGS)

# Ver o que o Fail2Ban está fazendo em tempo real
sudo journalctl -f -u fail2ban

# Ver quem está tentando logar no SSH (erros de senha)
sudo journalctl -f -u ssh

# Para o serviço do Fail2Ban
# 🚨 Só pare o serviço se for necessário, do contrário nem toque nisso
sudo systemctl stop fail2ban

# Inicia o serviço do Fail2Ban
# 🚨 Sempre que parar o serviço por algum motivo, inicie novamente
sudo systemctl start fail2ban
```

### UFW - Firewall Simples

A Hostinger tem um firewall na rede. É aconselhável ativá-lo. Mas também vamos
ativar o firewall em nosso próprio servidor.

```sh
# NO SERVIDOR
# Por que outro firewall? É o princípio de "defesa em profundidade".
# Ter um firewall no próprio host garante que, mesmo se a configuração do firewall
# da rede falhar ou for desativada, nosso servidor continua protegido.
# UFW (Uncomplicated Firewall) é uma interface amigável para o iptables do Linux.
sudo apt install ufw

# Por que 'deny incoming'? Esta é a política mais segura ("default deny").
# Bloqueamos TUDO por padrão e só liberamos explicitamente o que é necessário.
# Se você esquecer de bloquear uma porta, ela continua fechada.
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Liberamos a porta do SSH. Se não fizermos isso ANTES de ativar o firewall,
# seremos desconectados e não conseguiremos entrar mais.
sudo ufw allow ssh

# Liberamos as portas para tráfego web: 80 (HTTP) e 443 (HTTPS).
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Ative o firewall.
# Ele vai te alertar que conexões existentes podem ser derrubadas, mas como já
# liberamos a porta 'ssh', nossa conexão atual está segura.
sudo ufw enable
sudo ufw status
sudo ufw status verbose
```

---

### Clone o repository no servidor

Precisamos clonar o repositório do projeto. Os comandos abaixo vão ajudar com
isso.

É interessante que você faça um fork do projeto para sua conta, estou usando a
minha.

```sh
# NO SERVIDOR
# Por que uma nova chave? Esta chave SSH tem um propósito diferente.
# A primeira ('id_hostinger') era para NÓS acessarmos o SERVIDOR.
# Esta nova chave ('repository') é para o SERVIDOR acessar o GITHUB.
# É uma "chave de deploy".
ssh-keygen -t ed25519 -a 100 -f ~/.ssh/repository -C "${USER}"

# Copie a chave pública
cat ~/.ssh/repository.pub

# NO GITHUB (Repositório > Settings > Deploy Keys)
# Por que 'Deploy Key'? Uma deploy key dá acesso a APENAS UM repositório.
# É muito mais seguro do que usar sua chave SSH pessoal no servidor. Se o
# servidor for comprometido, o dano é contido apenas àquele repositório.
# Cole a chave pública que você copiou na nova Deploy Key.

# NO SERVIDOR
# Vamos criar outro "apelido" no SSH, desta vez para o GitHub.
vim ~/.ssh/config

###############################################################################
### Início do ~/.ssh/config ###################################################
###############################################################################

# ... Podem existir outros blocos aqui ...

# Cole o seguinte. Isso instrui o SSH a usar nossa 'repository' key
# sempre que se conectar ao 'github.com'.
Host github.com
  IgnoreUnknown AddKeysToAgent,UseKeychain
  AddKeysToAgent yes
  HostName github.com
  User git
  Port 22
  IdentityFile ~/.ssh/repository

# ... Podem existir outros blocos aqui ...

###############################################################################
### Fim do ~/.ssh/config ######################################################
###############################################################################

# Adiciona a "impressão digital" do github.com aos hosts conhecidos.
# Isso evita aquela pergunta "Are you sure you want to continue connecting?"
# na primeira vez que o git se conectar, o que quebraria nosso script de deploy.
ssh-keyscan github.com >> ~/.ssh/known_hosts
```

Agora é só clonar o repositório

```sh
# NO SERVIDOR
cd /dockerlabs
# Clonamos o repositório para o diretório atual (indicado pelo '.')
git clone URL_REPOSITORIO . # <- O ponto é importante aqui
```

---

### GHCR - GitHub Container Registry

Se o seu repositório for privado, você vai precisar criar um **PAT** Classic
(Personal Access Token) para baixar as imagens do Docker.

No seu perfil, acesse `Settings`, `Developer Settings` e crie o novo **PAT**
classic com as permissões `read:packages`.

Copie o token e digite o seguinte no server.

```sh
# NO SERVIDOR
# Por que isso? O Docker precisa se autenticar no GitHub Container Registry (GHCR)
# para baixar imagens de repositórios privados. O PAT (Personal Access Token)
# funciona como uma senha específica para essa tarefa.
echo "COLE_O_TOKEN_AQUI" | docker login ghcr.io -u SEU_USUARIO_GITHUB --password-stdin
# Isso deve alertar que o token ficará visível. Mas não tenho problemas com isso.
# Se seu servidor for invadido, isso não será seu maior problema (vai por mim).
```

---

## Subindo o projeto no servidor

### Copie o `.env.example` para `.env`

Ajuste o `.env` do projeto.

```sh
# NO SERVIDOR
cd /dockerlabs

# Por que gerar um secret? Este token será usado para verificar se o webhook
# que chega da GitHub Actions é legítimo, e não uma requisição falsa de
# um terceiro. É a "senha" que o GitHub e nossa API compartilham.
# Gere um, copie e cole no .env na variável GITHUB_WEBHOOK_SECRET.
python3 -c "import secrets; print(secrets.token_hex(32))"

cp .env.example .env
# Abra o arquivo e configure tudo.
vim .env
# Mantenha o CURRENT_ENV como development por agora para os testes iniciais.
```

Confira duas ou três vezes, porque editar o `.env` depois que a imagem está
pronta é bem chato.

---

### As imagens no `compose.yaml`

🚨 ATENÇÃO AQUI - Se você errar a URL das imagens não vai funcionar.

O arquivo do docker `compose.yaml` está configurado para o meu próprio
repositório. Abra este arquivo e altere todas as imagens para o seu nome de
usuário no GitHub.

Você pode obter as novas urls no seu repositório, em `Packages`. Ou você também
poderia usar outro registry qualquer, mas aí mudaria outras coisas também (como
nosso GitHub Actions).

```yaml
services:
  data_vol:
    # No seu repositório, vá em packages e pegue a URL para a imagem data_vol
    # Troque a imagem abaixo para a sua (se não, não vai funcionar)
    image: ghcr.io/luizomf/vps_deploy_template-data_vol:latest
  # ... várias outras configs

  dockerlabs:
    pull_policy: always
    # No seu repositório, vá em packages e pegue a URL para a imagem dockerlabs
    # Troque a imagem abaixo para a sua (se não, não vai funcionar)
    image: ghcr.io/luizomf/vps_deploy_template-dockerlabs:latest
  # ... várias outras configs

  nginx:
    container_name: nginx
    hostname: nginx
    pull_policy: always
    # No seu repositório, vá em packages e pegue a URL para a imagem nginx
    # Troque a imagem abaixo para a sua (se não, não vai funcionar)
    image: ghcr.io/luizomf/vps_deploy_template-nginx:latest
  # ... várias outras configs

  certbot:
    container_name: certbot
    hostname: certbot
    pull_policy: always
    # No seu repositório, vá em packages e pegue a URL para a imagem certbot
    # Troque a imagem abaixo para a sua (se não, não vai funcionar)
    image: ghcr.io/luizomf/vps_deploy_template-certbot:latest

  # ... várias outras configs
```

Salve o arquivo e reserve, vamos cozinhar outras coisas para usar isso depois.

---

### Bootstrap `development` (primeira vez)

Configure mais uma vez o `.env`, mantenha o `CURRENT_ENV` como `development`
para testes iniciais. E execute o seguinte script.

```sh
# NO SERVIDOR
# O que este script faz? Ele é um "inicializador". Ele lê o .env, gera as
# configurações do NGINX a partir dos templates, cria os certificados SSL
# (certificados de teste, no modo 'development') e sobe os contêineres
# pela primeira vez. Ele prepara todo o ambiente.
cd /dockerlabs
/dockerlabs/data/scripts/bootstrap
```

---

### Bootstrap `production` (segunda e última vez)

Depois que tudo funcionar em `development`, mude `CURRENT_ENV` para `production`
e execute novamente.

🚨 Aqui você precisa ter absoluta certeza que tudo está certo no `.env`,
principalmente seu(s) domínio(s).

Os certificados SSL serão gerados pelo certbot.

```sh
# NO SERVIDOR
# Por que rodar de novo em 'production'? No modo 'production', o script
# irá instruir o Certbot a gerar certificados SSL REAIS e válidos para o seu
# domínio, em vez dos certificados de teste usados anteriormente.
cd /dockerlabs
/dockerlabs/data/scripts/bootstrap
```

---

### Watcher no servidor

Vamos criar um serviço para ler arquivos que a `FastAPI` salvar em uma pasta.

Execute o seguinte:

```sh
# Crie o arquivo do serviço
# Por que 'systemd'? É o gerenciador de serviços padrão no Linux moderno.
# Criar um serviço para nosso script 'watcher' garante que ele:
# 1. Inicie automaticamente quando o servidor ligar.
# 2. Reinicie sozinho se por algum motivo ele falhar.
# 3. Tenha seus logs gerenciados pelo 'journalctl'.
# É a forma robusta de rodar um processo em segundo plano.
sudo vim /etc/systemd/system/webhook-watcher.service

###############################################################################
### Início do /etc/systemd/system/webhook-watcher.service #####################
###############################################################################

[Unit]
# Descrição do nosso serviço.
Description=Webhook Watcher for Docker Deployment
# Garante que este serviço só inicie depois que a rede estiver pronta.
After=network.target

[Service]
Type=simple
# O diretório de trabalho para o nosso script.
WorkingDirectory=/dockerlabs/
# O comando que será executado.
ExecStart=/dockerlabs/data/scripts/watcher
# Reinicia o serviço sempre que ele parar (seja por falha ou sucesso).
Restart=always
# Espera 3 segundos antes de tentar reiniciar.
RestartSec=3
# Executa o serviço com nosso usuário, não como root. (Princípio do Menor Privilégio)
User=SEU_USUARIO_SERVER
Group=SEU_USUARIO_SERVER

[Install]
# Diz ao systemd para iniciar este serviço durante o boot "normal" do sistema.
WantedBy=multi-user.target

###############################################################################
### Fim do /etc/systemd/system/webhook-watcher.service ########################
###############################################################################

# Agora execute os comandos abaixo em ordem
# Recarrega o systemd para ele ler nosso novo arquivo de serviço.
sudo systemctl daemon-reload
# Habilita o serviço para iniciar no boot.
sudo systemctl enable webhook-watcher
# Inicia o serviço agora.
sudo systemctl start webhook-watcher
# Verifica o status para ver se está rodando sem erros.
sudo systemctl status webhook-watcher

# # Se precisar remover este serviço por algum motivo, use
# # os comandos abaixo.
# sudo systemctl stop webhook-watcher
# sudo systemctl disable webhook-watcher
# sudo rm /etc/systemd/system/webhook-watcher.service
# sudo systemctl daemon-reload
# # Se insistir em não apagar
# sudo systemctl reset-failed

# Para ver os logs do nosso watcher em tempo real.
sudo journalctl -u webhook-watcher.service -f
```

---

## GitHub Action

A `FastAPI` precisará de um secret. Nós geramos um lá no começo deste texto e
adicionamos no `.env`. Esses secrets precisam estar no repositório.

Acesse `Settings` > `Secrets and variables` > `New Repository Secret`.

Crie esses secrets:

- `DEPLOY_WEBHOOK_URL` - https://DOMINIO_SERVER/webhook/github
- `DEPLOY_WEBHOOK_SECRET` - Cole o `GITHUB_WEBHOOK_SECRET` do `.env` (mesmo
  valor)

**Por que usar secrets do GitHub?**

Para evitar colocar informações sensíveis (como a URL do webhook e a senha)
diretamente no código do workflow.

O GitHub injeta esses valores de forma segura durante a execução da Action. O
`DEPLOY_WEBHOOK_SECRET` deve ser exatamente o mesmo que está no seu arquivo
`.env` para que a assinatura do webhook possa ser validada com sucesso.

Se tudo estiver correto, ao fazer push para o branch `main`, os testes da
aplicação serão executados, as builds de imagens do Docker serão criadas no GHCR
e o `webhook` será chamado para alertar o servidor que existe um deploy para ser
feito.

---
