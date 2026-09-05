# AI Coding Server

An AI coding-task control plane. The product accepts a repository task,
executes an agent through controlled tools in an isolated sandbox, verifies the
result, and preserves a reviewable audit trail and Git diff.

The implementation roadmap is in [docs/implementation-plan.md](docs/implementation-plan.md).
The source requirements are [docs/ai-srs.md](docs/ai-srs.md).

## Repository layout

- `backend/` — FastAPI control plane, domain/application layers, and worker.
- `frontend/` — React dashboard (to be added in the UI phase).
- `infra/` — local platform and sandbox deployment definitions.
- `tests/` — cross-cutting end-to-end tests and fixtures.
- `docs/` — specifications and architecture decisions.

## Current milestone

The repository is now scaffolded for Phase 0. The first implementation slice
will be a tested FastAPI health endpoint, typed configuration, logging, and the
task state-machine domain model.
