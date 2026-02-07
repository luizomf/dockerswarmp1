# Changelog

All notable changes to this project are documented here. This file records
**what changed**, not discussion or rationale.

## Unreleased

- Initial project setup
- Added root AGENTS.md defining AI workflow rules
- Established CHANGELOG.md as the single source of change history
- Aligned package metadata with module name and fixed test imports
- Added Swarm stack definition with Traefik, API, frontend, and Postgres
- Added Swarm env placeholders for Traefik domains and Postgres credentials
- Switched Traefik routing to a single public domain with API path prefix
- Documented node inventory and domain mapping
- Updated default public domain to use a subdomain
- Adjusted Traefik and Postgres update strategy for Swarm host ports
- Switched Traefik to the Swarm provider and external overlay networks
- Fixed CI workflow Dockerfile path for API builds
- Documented local run steps and exposed API port in Compose
- Fixed GHCR image tagging to avoid invalid references
- Pointed webhook job storage to NFS-mounted path
- Added swarm deploy watcher scripts and Just recipes
- Added nginx-based frontend image for Swarm
- Switched webhook and database passwords to Swarm secrets
- Updated Postgres volume mount for v18 data layout
- Forced Traefik to use a modern Docker API version
- Added visit counter endpoint backed by Postgres
- Fixed Traefik API routing to keep /api prefix
- Fixed Postgres DSN building for passwords with spaces
- Updated frontend landing page copy for the Swarm project
- Added /api prefix alias for the GitHub webhook endpoint
- Expanded README with full Swarm setup and troubleshooting guide
- Documented NFS permissions and post-reboot checklist in README
- Removed PDF manuals from the repository
- Documented systemd automount options for NFS mounts (boot reliability)
- Documented scaling guidance and resource limits for the Swarm stack
- Documented how to measure short-burst request rate safely (RPS vs connections)
- Added a practical end-to-end video recording outline under docs/
- Added DEV_GUIDE.md and a detailed video script to keep README/video focused
- Refined the video hook to delay tradeoffs and added Mermaid diagrams (runtime + deploy)
- Reworked the first 60 seconds into high-tempo beats and added Traefik pronunciation note
- Added a full local Docker Compose dev stack (Traefik + API + frontend + Postgres)
- Simplified Justfile recipes (kept only essential Compose/Swarm/watcher commands)
- Added a guardrail prompt for Gemini second opinions (no tools / no repo touch)
- Added a rebuild manual covering safe node removal and full cluster rebuild order
- Expanded rebuild manual with the kvm8 (last node) shutdown/leave sequence before formatting
- Hardened VPS bootstrap script/docs (safer SSH restart, optional NOPASSWD sudo, WireGuard-only Swarm ports)
- Added VPS post-bootstrap verification checklist (WireGuard/SSH/UFW/fail2ban/NOPASSWD)
- Made VPS bootstrap script rerunnable via flags (skip apt upgrade, skip UFW reset) and added stricter input validation
- Switched CI build/deploy workflow to manual trigger (workflow_dispatch) to avoid GHCR limits on every push
- Cleaned the deploy workflow matrix to only build the services used by this repo
- Documented the "tighten UFW to wg0-only" follow-up step for existing VPS rules
- Added concrete UFW migration commands to move Swarm/NFS rules from public IPs to wg0-only
- Added an ideas inbox under docs/ to capture improvements without derailing PLAN.md
- Documented the ideas inbox workflow in AGENTS.md

## 2026-02-05

- Introduced PLAN.md as a temporary planning artifact
- Defined lifecycle rule: PLAN.md is removed after execution
- Added infra/AGENTS.md to scope infrastructure-related instructions

## 2026-02-04

- Created initial repository structure
- Configured base tooling and scripts
