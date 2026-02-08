# Docker Swarm Demo (Hostinger 3x VPS)

Projeto demonstrativo de um cluster Docker Swarm com 3 nós, Traefik (Edge), API (FastAPI), Frontend (Nginx/SPA) e PostgreSQL.

> 🚀 **Deploy Confirmado:** Este projeto foi testado e validado ao vivo em 3 VPS KVM 2 da Hostinger.

## 📚 Documentação (Comece Aqui)

Não tente adivinhar. Siga os manuais testados:

| Documento | Objetivo | Público Alvo |
| :--- | :--- | :--- |
| **[`docs/MANUAL_DO_VIDEO.md`](docs/MANUAL_DO_VIDEO.md)** | **Guia Passo a Passo Completo** (O "Script" do Vídeo). Cobre formatação, SSH, WireGuard, NFS, Swarm e Deploy. | **Todos** |
| [`DEV_GUIDE.md`](DEV_GUIDE.md) | Guia detalhado de desenvolvimento e conceitos por trás das escolhas. | Devs / Curiosos |
| [`docs/REBUILD_MANUAL.md`](docs/REBUILD_MANUAL.md) | Runbook para recuperar o cluster em caso de desastre ou re-deploy limpo. | Ops / SysAdmin |
| [`docs/SECURITY_REVIEW.md`](docs/SECURITY_REVIEW.md) | Análise de segurança, hardening aplicado e riscos residuais. | Security |

## 🏗️ Arquitetura

- **3 Nós Swarm (Managers):** Conectados via VPN privada (WireGuard).
- **Edge (kvm8):** Nó principal que expõe portas 80/443 (Traefik) e segura o Banco de Dados.
- **Workers (kvm2, kvm4):** Processam a carga da API e Frontend.
- **Rede:** `internal` (Overlay) fechada para o mundo, `public` (Overlay) apenas para o Traefik.
- **Storage:** NFSv4 sobre WireGuard para compartilhamento de arquivos entre nós.

## ⚡ Quick Start (Local Development)

Quer rodar no seu computador sem subir 3 servidores? Use o Docker Compose (simula o stack).

1. **Clone e Configure:**
   ```bash
   git clone https://github.com/luizomf/dockerswarmp1.git
   cd dockerswarmp1
   cp .env.example .env
   ```

2. **Suba o ambiente (com `just`):**
   ```bash
   just upb
   ```
   *(Ou `docker compose -f docker/compose.yaml up --build`)*

3. **Acesse:**
   - Frontend: http://app.localhost
   - API: http://app.localhost/api/visit

## 🛠️ Comandos Úteis (Production)

Se você já está no nó manager (`kvm8`):

```bash
# Deploy / Atualização
set -a; source .env; set +a
just stack-deploy

# Logs
just stack-logs api
just stack-logs traefik

# Status
docker stack ps dockerswarmp1
docker node ls
```

---
*Projeto patrocinado pela Hostinger. Código livre (MIT).*