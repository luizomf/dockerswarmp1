# Current Plan

## Task: Migrate project to Docker Swarm (first deployable stack)

Create the first Swarm-ready stack for the project (Traefik + FastAPI + PostgreSQL 18
+ frontend), replacing the old compose/nginx flow. Ensure placement constraints for
fixed services on KVM8, and prepare env/secrets for GHCR pull-based deploys.

Current Date: 2026-02-05

- [x] Step 1: Analyze current compose/Dockerfiles and list Swarm deltas.
- [x] Step 2: Define the Swarm stack file (services, networks, volumes, constraints).
- [x] Step 3: Add/adjust app envs and secrets needed for Swarm (Traefik, DB, API).
- [ ] Step 4: Verify local build/run expectations (no nginx, API + DB + frontend).
- [ ] Step 5: Update CHANGELOG.md (once implementation starts).
- [ ] Step 6: Clear PLAN.md (remove all completed content when done).

_(Note: Once all items are checked `[x]`, this file should be cleared for the
next task)_
