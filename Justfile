set shell := ["bash", "-cu"]
set dotenv-load := true

compose_file := "docker" / "compose.yaml"
env_file := ".env"
stack_file := "docker" / "stack.yaml"
stack_name := "dockerswarmp1"

# List all just recipes
@default:
  @just -l

_dc *ARGS:
  docker compose -f {{ compose_file }} --env-file {{ env_file }} {{ ARGS }}

_dcb *ARGS:
  docker compose -f {{ compose_file }} --env-file {{ env_file }} build {{ ARGS }}

_dce *ARGS:
  docker compose -f {{ compose_file }} --env-file {{ env_file }} exec {{ ARGS }}

_dcr *ARGS:
  docker compose -f {{ compose_file }} --env-file {{ env_file }} run {{ ARGS }}

# Docker compose down
down *ARGS:
  just _dc -f {{ compose_file }} --env-file {{ env_file }} down {{ ARGS }}

# Down first, then docker compose up --detach (-d)
downupd *ARGS: down
  just upd {{ ARGS }}

# Down first, then build
downupb *ARGS: down
  just upb {{ ARGS }}

# Down first, then watch
downupw *ARGS: down
  just upw {{ ARGS }}

# Docker compose up
up *ARGS:
  just _dc up {{ ARGS }}

# Docker compose up --detach (-d)
upd *ARGS:
  just _dc up -d {{ ARGS }}

# Docker compose up -d --build
upb *ARGS:
  just build
  just upd --remove-orphans {{ ARGS }}

# Docker compose up --watch
upw *ARGS:
  just _dc up --watch {{ ARGS }}

# Build everything
build:
  # just _dcb data_vol
  just _dcb

# Docker compose exec {{ ARGS }}
e *ARGS:
  just _dce {{ ARGS }}

# Docker compose exec -it {{ ARGS }}
et *ARGS:
  just e {{ ARGS }}

# Docker compose exec -it nginx sh {{ ARGS }}
enginx *ARGS:
  just et nginx sh {{ ARGS }}

# Docker compose exec -it data_vol sh {{ ARGS }}
# edatavol *ARGS:
#   just et data_vol sh {{ ARGS }}

# Docker compose exec -it dockerlabs bash {{ ARGS }}
edockerlabs *ARGS:
  just et dockerlabs bash {{ ARGS }}

# Docker compose exec -it certbot sh {{ ARGS }}
ecertbot *ARGS:
  just et certbot sh {{ ARGS }}

# Docker compose run {{ ARGS }}
r *ARGS:
  just _dcr --rm {{ ARGS }}

# Docker compose run -it {{ ARGS }}
rt *ARGS:
  just r -it {{ ARGS }}

# Docker compose run -it nginx sh {{ ARGS }}
rnginx *ARGS:
  just rt nginx sh {{ ARGS }}

# Docker compose run -it data_vol sh {{ ARGS }}
# rdatavol *ARGS:
#   just rt data_vol sh {{ ARGS }}

# Docker compose run -it dockerlabs bash {{ ARGS }}
rdockerlabs *ARGS:
  just rt dockerlabs bash {{ ARGS }}

# Docker compose run -it certbot sh {{ ARGS }}
rcertbot *ARGS:
  just rt certbot sh {{ ARGS }}

# 🚨 Docker compose down, delete all volumes and orphan containers
nukevolumes:
  just down -v --remove-orphans
  docker volume prune -f

# 🚨 Docker compose down, delete all volumes and orphan containers then build
nukevolumesbuild: nukevolumes
  just build

# 🚨 Basically delete all volumes, build all and up -d
nukevolumesupb: nukevolumes
  just upb

# 🚨 Try to remove everything: volumes, images, containers... and prune the system and then build
nukeallbuild: nukeall
  just build

# 🚨 nukeall + upb
nukeallupb: nukeall
  just upb

# 🚨 Try to remove everything: volumes, images, containers... and prune the system
nukeall: nukevolumes && nukeimages
  docker builder prune -f
  docker system prune -f
  docker buildx history rm --all

# 🚨 Docker compose down, delete all images and orphan containers
nukeimages:
  just down --rmi all --remove-orphans
  docker image prune -f

# Swarm
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
