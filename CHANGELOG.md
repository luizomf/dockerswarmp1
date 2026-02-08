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
- Added a rebuild manual covering safe node removal and full cluster rebuild order
- Expanded rebuild manual with the kvm8 (last node) shutdown/leave sequence before formatting
- Hardened VPS bootstrap script/docs (safer SSH restart, optional NOPASSWD sudo, WireGuard-only Swarm ports)
- Added VPS post-bootstrap verification checklist (WireGuard/SSH/UFW/fail2ban/NOPASSWD)
- Made VPS bootstrap script rerunnable via flags (skip apt upgrade, skip UFW reset) and added stricter input validation
- Switched CI build/deploy workflow to manual trigger (workflow_dispatch) to avoid GHCR limits on every push
- Cleaned the deploy workflow matrix to only build the services used by this repo
- Added a security review report under docs/
- Disabled FastAPI OpenAPI/docs endpoints in production (reduce public attack surface)
- Added basic security headers to the frontend Nginx config (nosniff, frame deny, referrer policy)
- Bound the local Traefik dashboard port to 127.0.0.1 in Compose (avoid accidental LAN exposure)
- Added safety checks to the deploy watcher to avoid dangerous deletes if misconfigured
- Added a retry path for transient Postgres disconnects on /api/visit
- Documented Docker log rotation and log reset commands in the rebuild manual
- Returned the responding container hostname in /api/visit and displayed it on the frontend
- Documented the "tighten UFW to wg0-only" follow-up step for existing VPS rules
- Added concrete UFW migration commands to move Swarm/NFS rules from public IPs to wg0-only
- Added an ideas inbox under docs/ to capture improvements without derailing PLAN.md
- Documented the ideas inbox workflow in AGENTS.md
- Extended the inbox workflow with Owner+Files to avoid conflicts and coordinate Gemini tasks
- Removed the stored Gemini prompt doc; use inline prompts and the inbox owner workflow
- Documented explicit ownership rules for PLAN.md (Codex) and docs/INBOX.md (user)
- Fixed rebuild manual gaps (repo checkout under /opt and NFS setup before stack deploy)
- Documented that group membership changes require relogin/newgrp (prevents NFS "permission denied" confusion)
- Routed Traefik backend traffic through the internal overlay network (app services no longer attach to the public overlay)
- Fixed Traefik Swarm provider flag spelling (avoid runtime "unknown flag" errors)
- Redesigned the frontend landing page (Hostinger coupon CTA, architecture overview, quick test commands)
- Expanded the rebuild manual with a video-ready runbook (clone, .env, GHCR auth, secrets, deploy, validation, watcher)
- Clarified in the rebuild manual that kvm8 must mount /mnt/nfs before starting the watcher (avoids mkdir permission errors)
- Documented that draining/rebooting kvm8 causes full downtime in the rebuild manual
- Documented that docker stack deploy does not read .env (use just or export vars first)
- Added an external test note for validating visit counts with third-party site checks
- Allowed unique container hostnames in local Compose by removing fixed API hostname/container_name
- Added a Just recipe to scale the API service locally for hostname demo
- Stripped Server header via Traefik middleware (API + frontend)
- Added a Just recipe to list API containers across kvm2/kvm4/kvm8 via SSH
- Added Just recipes to reset the local Compose stack and wipe volumes with explicit confirmation
- Clarified VISIT_SALT behavior and fallback in .env.example
- Ignored .env.* files (except .env.example) to prevent accidental local env commits
- Summarized key security review highlights and trade-offs in README
- Clarified local Compose routes (Traefik host rule) and manual CI trigger in README
- Clarified which guide to use (DEV_GUIDE vs VPS_BOOTSTRAP vs REBUILD_MANUAL) in README
- Clarified Compose vs Swarm expectations and WireGuard example caveats in docs
- Fixed mobile horizontal overflow on the stats panel by wrapping flex items and allowing the container id to wrap

## 2026-02-07

- Created `docs/MANUAL_DO_VIDEO.md` documenting the full live deploy process
- Switched API volume from NFS driver to Bind Mount to fix permission errors
- Updated `README.md` to index documentation and point to the video manual
- Documented step-by-step Swarm setup, WireGuard, NFS, and Hardening in the new manual

## 2026-02-05

- Introduced PLAN.md as a temporary planning artifact
- Defined lifecycle rule: PLAN.md is removed after execution
- Added infra/AGENTS.md to scope infrastructure-related instructions

## 2026-02-04

- Created initial repository structure
- Configured base tooling and scripts