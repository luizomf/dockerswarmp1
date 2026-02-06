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

## 2026-02-05

- Introduced PLAN.md as a temporary planning artifact
- Defined lifecycle rule: PLAN.md is removed after execution
- Added infra/AGENTS.md to scope infrastructure-related instructions

## 2026-02-04

- Created initial repository structure
- Configured base tooling and scripts
