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



