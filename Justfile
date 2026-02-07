set shell := ["bash", "-cu"]
set dotenv-load := true

compose_file := "docker/compose.yaml"
env_file := ".env"
stack_file := "docker/stack.yaml"
stack_name := "dockerswarmp1"

@default:
  @just -l

################################################################################
# Local Development (Docker Compose)
################################################################################

compose *ARGS:
  docker compose -f {{ compose_file }} --env-file {{ env_file }} {{ ARGS }}

build *ARGS:
  just compose build {{ ARGS }}

up *ARGS:
  just compose up {{ ARGS }}

upd *ARGS:
  just compose up -d {{ ARGS }}

upb *ARGS:
  just compose up -d --build --remove-orphans {{ ARGS }}

upb-scale-api COUNT="3":
  just compose up -d --build --remove-orphans --scale api={{ COUNT }}

down *ARGS:
  just compose down {{ ARGS }}

ps:
  just compose ps

logs *ARGS:
  just compose logs -f --tail=200 {{ ARGS }}

sh SERVICE *ARGS:
  just compose exec -it {{ SERVICE }} sh {{ ARGS }}

################################################################################
# Swarm (Production)
################################################################################

swarm-networks:
  docker network create --driver=overlay --attachable public
  docker network create --driver=overlay --attachable --internal internal

swarm-label-kvm8:
  docker node update --label-add role=kvm8 kvm8

stack-deploy:
  docker stack deploy -c {{ stack_file }} {{ stack_name }} --with-registry-auth

stack-rm:
  docker stack rm {{ stack_name }}

stack-ps:
  docker stack ps {{ stack_name }}

stack-services:
  docker stack services {{ stack_name }}

stack-logs SERVICE:
  docker service logs {{ stack_name }}_{{ SERVICE }}

stack-api-containers:
  #!/bin/bash
  for host in kvm2 kvm4 kvm8; do \
    echo "==> $host"; \
    ssh "$host" 'docker ps --filter name=dockerswarmp1_api'; \
    echo ""; \
  done

################################################################################
# Watcher (Systemd on kvm8)
################################################################################

watcher-install:
  sudo cp scripts/webhook-watcher.service /etc/systemd/system/webhook-watcher.service
  sudo systemctl daemon-reload
  sudo systemctl enable --now webhook-watcher

watcher-status:
  sudo systemctl status webhook-watcher

watcher-logs:
  sudo journalctl -u webhook-watcher -f

watcher-uninstall:
  sudo systemctl disable --now webhook-watcher
  sudo rm -f /etc/systemd/system/webhook-watcher.service
  sudo systemctl daemon-reload
