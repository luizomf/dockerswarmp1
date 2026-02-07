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

