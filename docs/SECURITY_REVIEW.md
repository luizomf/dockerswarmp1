# Security Review (Swarm + Traefik + FastAPI + Nginx)

Date: 2026-02-07

Scope:

- VPS hardening (UFW, SSH, fail2ban)
- Swarm + Traefik exposure (published ports, overlay networks)
- FastAPI API (webhook verification, secrets handling, public endpoints)
- Static frontend (HTML/CSS/JS) + Nginx config

This is a "production-ish demo" baseline. It is intentionally not Netflix-grade
HA or zero-trust, but it should not be an open door either.

## Executive Summary

What is good:

- Only Traefik publishes `:80`/`:443` in Swarm; API/frontend/Postgres are not
  published publicly by Swarm. See `docker/stack.yaml` (Traefik ports at
  `docker/stack.yaml:13-48` and null ports for other services at
  `docker/stack.yaml:50-114`).
- Traefik uses Swarm provider with `exposedByDefault=false`, and backend traffic
  is routed via the internal overlay network (`--providers.swarm.network=internal`)
  so app services do not need to attach to the public overlay. See
  `docker/stack.yaml:17-41`.
- FastAPI webhook endpoint validates GitHub signatures using HMAC SHA256 and
  constant-time compare. See `src/dockerswarmp1/main.py:184-198`.
- FastAPI docs/OpenAPI are disabled in production to reduce public attack
  surface. See `src/dockerswarmp1/main.py:32-42`.
- Frontend is static and does not inject untrusted HTML. It updates the visit
  count via `textContent`. See `frontend/index.html:216-229`.
- Nginx adds basic security headers and hides server tokens. See
  `frontend/default.conf:6-13`.

What still matters (trade-offs / residual risk):

- The stack has a known SPOF: `kvm8` runs Traefik + Postgres + NFS. Draining or
  rebooting `kvm8` is full downtime for the demo.
- The visit counter endpoint is public and writes to Postgres. Without
  rate-limiting, it can be abused to grow the table.
- NFS permissions are convenient for a demo, but would be a serious concern in
  a real production environment (see Finding SRV-001).

## Findings

### SRV-001: NFS export uses `no_root_squash`

Rule ID: INFRA-NFS-001

Severity: High

Location:

- Runtime config on `kvm8` (`exportfs -v` shows `no_root_squash`)

Evidence:

- Example `exportfs -v` output (kvm8):
  `/srv/nfs/swarm_data 10.100.0.0/24(...,rw,...,no_root_squash,...)`

Impact:

- If any node is compromised, root on that node can act as root on the NFS
  export, enabling tampering with shared data (including the webhook job queue).

Fix:

- Prefer `root_squash` and explicit UID/GID mapping, or avoid NFS for anything
  that can trigger deployment side effects (use a queue inside the manager node
  only, or use a proper message queue).

Mitigation:

- Keep NFS reachable only on `wg0` (already the case).
- Treat all nodes in the WireGuard network as a single trust zone.

False positive notes:

- This is an intentional demo trade-off. It is still important to document it
  clearly for real production use.

### SRV-002: Deploy watcher effectively has root-equivalent privileges

Rule ID: INFRA-DEPLOY-001

Severity: High

Location:

- `scripts/webhook-watcher.service` (deploy command) and host permissions

Evidence:

- `scripts/webhook-watcher.service:10-16` runs:
  `DEPLOY_COMMAND="just stack-deploy"`
- The watcher must be able to run Docker commands on the host, which typically
  means membership in the `docker` group (root-equivalent on that host).

Impact:

- If an attacker can trigger deploys (by stealing the webhook secret, taking
  over the repo, or taking over the CI), they can replace images and run code in
  the cluster.

Fix:

- Use GitHub Actions OIDC + a pull-based deployment (server polls GHCR digest or
  tags) or require an explicit human approval step.
- Run the watcher as a dedicated user with narrowly-scoped permissions (hard in
  practice with Docker).

Mitigation:

- Webhook signature verification is already in place (see SRV-005).
- Keep the webhook secret out of logs and out of the repo (Swarm secret + repo
  secret is correct).

### SRV-003: `X-Forwarded-For` is trusted for "unique visit" identity

Rule ID: FASTAPI-INPUT-001

Severity: Medium

Location:

- `src/dockerswarmp1/main.py:121-129`

Evidence:

- `get_client_ip()` reads `x-forwarded-for` and uses the first value.

Impact:

- If a client can influence the `X-Forwarded-For` header, the "unique visits"
  counter can be trivially inflated and can cause more DB writes than expected.

Fix:

- Ensure the edge proxy strips incoming `X-Forwarded-For` and sets it itself.
- Alternatively, derive identity from `request.client.host` and configure
  Uvicorn/Trafik "trusted proxy" settings correctly.

Mitigation:

- This endpoint is demo-only and does not gate auth/permissions.

### SRV-004: Public `/api/visit` can be abused to grow the DB table

Rule ID: FASTAPI-DOS-001

Severity: Medium

Location:

- `src/dockerswarmp1/main.py:140-157` (insert + count)
- `src/dockerswarmp1/main.py:175-182` (public endpoint)

Evidence:

- The handler inserts one row per `(visit_date, visitor_hash)` and exposes the
  endpoint publicly.

Impact:

- An attacker can generate many unique hashes (vary user-agent and/or
  `X-Forwarded-For`) and grow the `visit_events` table, increasing I/O and disk
  usage.

Fix:

- Add rate limiting at the edge (Traefik middleware) for `/api/visit`.
- Add a retention policy (daily cleanup job) or store aggregated counters rather
  than per-visitor rows.

Mitigation:

- Keep Postgres pinned and monitored for disk usage (out of scope for the demo).

### SRV-005: Webhook signature verification looks correct

Rule ID: FASTAPI-WEBHOOK-001

Severity: Info

Location:

- `src/dockerswarmp1/main.py:184-225`

Evidence:

- HMAC SHA256 computed from raw body and compared with `hmac.compare_digest`.
- Only `push` events for `refs/heads/main` enqueue a deploy.

Impact:

- This is a positive finding (reduces risk of unauthorized deploy triggers).

### SRV-006: Dev-only Traefik dashboard is still enabled in Compose (restricted to localhost)

Rule ID: TRAEFIK-DEV-001

Severity: Low

Location:

- `docker/compose.yaml:13-29`

Evidence:

- `--api.insecure=true` is enabled for local dev.
- Port mapping is bound to `127.0.0.1:8080` (so it is not exposed to the LAN by
  default).

Impact:

- If someone copies this Compose file to a server and changes the binding, they
  can accidentally expose an insecure dashboard.

Fix:

- Keep it dev-only and explicitly call it out (already done in comments).

### SRV-007: Inline JS and inline handlers reduce CSP options (no XSS found)

Rule ID: JS-CSP-001

Severity: Low

Location:

- `frontend/index.html:52-55` (inline `onclick`)
- `frontend/index.html:216` (inline `<script>`)

Evidence:

- Inline JS and inline handlers are present.

Impact:

- Not a vulnerability by itself here (content is static), but it makes it harder
  to enable a strict CSP later without refactors.

Fix:

- Move JS into a separate file and attach handlers via `addEventListener`.

## Optional Hardening Ideas (Not Implemented)

- Add Traefik rate limiting middleware to `/api/visit` and/or `/api/webhook/github`.
- Add `TrustedHostMiddleware` in FastAPI for stricter Host header validation.
- Consider disabling the `/` "hostname" response in production (`src/dockerswarmp1/main.py:160-167`).
- Consider removing NFS `no_root_squash` and limiting RPC services to `wg0`.

Assumption:
- This baseline assumes all nodes reachable via WireGuard are within the same
  trust zone. If you need zero-trust between nodes, the architecture must
  change (e.g., stronger isolation, least-privilege storage, different deploy
  trigger model).
