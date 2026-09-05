# AI Coding Server Implementation Plan

## 1. Purpose and MVP definition

The AI Coding Server is a control plane for an AI coding agent. A user submits
a coding task for a repository; a background worker runs the agent in an
isolated workspace; the platform records the session, tool activity,
verification results, and resulting Git diff for review.

The MVP is complete only when this end-to-end path works:

1. An authenticated user creates a project and registers a repository.
2. The user creates a task with a base branch, model, limits, and verification
   commands.
3. The API persists the task and sends work to a background queue.
4. A worker prepares an isolated sandbox and repository checkout.
5. The agent uses only validated, permitted tools to inspect, edit, and test
   the repository.
6. The worker records messages, tool calls, commands, logs, artifacts,
   verification runs, and the Git diff.
7. The user can inspect task state, activity, verification, and the diff.
8. The sandbox is cleaned up in success, cancellation, timeout, and failure
   cases.

Out of the first release: distributed execution, VM/Kubernetes isolation,
automatic Git push/merge or pull requests, complex multi-agent workflows,
and semantic repository indexing.

## 2. Architecture decisions

| Concern | Initial decision | Why |
| --- | --- | --- |
| Repository layout | Monorepo: Python backend and TypeScript web app | Keeps contracts, local infrastructure, and product delivery together while the product is small. |
| API | FastAPI, Pydantic v2, SQLAlchemy 2, Alembic | Typed Python API with mature async and migration support. |
| Durable state | PostgreSQL | Required relational/audit data needs transactional integrity. |
| Background work | Celery with Redis broker | HTTP stays responsive while coding tasks run for minutes. |
| Agent runtime | Custom Python ports-and-adapters layer | The model, tools, and sandbox must remain replaceable and explicitly controlled. |
| Sandbox | Docker on a dedicated Linux execution host | Meets MVP isolation needs while preserving a future SandboxBackend interface for stronger runtimes. |
| Repository operations | Git CLI behind a repository adapter | Reliable initial support for clone, branch, status, and diff without coupling domain code to command execution. |
| Files/artifacts | Object-store interface; MinIO locally | Prevents unbounded logs and reports from filling PostgreSQL rows. |
| UI | React, TypeScript, Vite | A focused dashboard for projects, task activity, verification, and diffs. |
| Realtime | Server-Sent Events initially | One-way task-event streaming is simpler than bidirectional WebSockets and meets the MVP need. |

## 3. Trust boundaries and non-negotiable rules

```text
Browser -> API/control plane -> PostgreSQL, Redis, object storage
                                 |
                                 | task command only
                                 v
                         Worker / agent runtime
                                 |
                                 | SandboxBackend interface
                                 v
                    Docker sandbox: /workspace/repository
```

- Model output is untrusted input. It never becomes a host command directly.
- Every tool has a schema, risk level, authorization policy, audit record, and
  execution timeout.
- All agent file and command activity is relative to the sandbox workspace.
- The sandbox receives no Docker socket, host home directory, application
  secrets, LLM keys, or arbitrary host mounts.
- Sandboxes run non-root, without privileged mode, with dropped capabilities,
  `no-new-privileges`, resource limits, timeouts, and restrictive networking.
- Task state changes are explicit and validated; terminal states are immutable.
- Git push, credential use, and other externally visible operations are not
  part of the MVP tool allowlist.

## 4. Domain model and lifecycle

The initial persistent aggregates are: users, projects, project members,
repositories, repository credentials (secret references only), model
providers/models, tasks, agent sessions/messages, tool definitions/calls,
sandboxes/executions, verification runs, diffs, artifacts, logs, and
permissions.

Task lifecycle:

```text
queued -> initializing -> running <-> verifying -> completed
                               |                 |
                               +-> failed/cancelled/timeout
```

Only the worker advances an accepted task beyond `queued`. Cancellation is a
requested state observed by the worker; cleanup happens before a task becomes
terminal. The API never waits for agent execution.

## 5. Package structure

```text
backend/src/ai_coding_server/
  api/          HTTP routes, dependencies, request/response schemas
  application/  use cases, state transitions, transactions, events
  domain/       entities, value objects, policies, ports
  infrastructure/ database, queue, storage, model, Docker, Git adapters
  worker/       Celery entrypoint and task handlers
  config/       typed configuration and logging
frontend/src/   React pages, API client, task-event stream, UI components
infra/          Docker Compose, sandbox image, local deployment assets
tests/          unit, integration, contract, and end-to-end suites
```

Dependencies point inward: API, worker, and infrastructure depend on
application/domain; domain depends on no framework. The agent calls tool and
sandbox *ports* owned by the domain/application layer, while Docker, Git,
storage, queues, and LLM SDKs implement those ports in infrastructure.

## 6. Delivery plan

### Phase 0 — foundation and executable architecture

- Create the monorepo, dependency manifests, formatting/lint/type-check/test
  tooling, environment template, Docker Compose, and CI.
- Define configuration, structured logs, correlation IDs, error envelope, and
  health/readiness endpoints.
- Define domain enums, task state transition policy, core ports, and API
  versioning conventions.
- Exit criterion: API and worker boot locally; tests, linting, and type checks
  run in CI; no real sandbox or model call is required.

### Phase 1 — identity, projects, repositories, and task submission

- Add migrations for users, project membership, repositories, models, and
  tasks.
- Implement authentication and project-level role authorization.
- Implement project/repository/task API contracts and ownership checks.
- Persist task creation transactionally, then enqueue only accepted tasks.
- Exit criterion: an authorized user can create and view project, repository,
  and queued task records with audit events.

### Phase 2 — execution control plane

- Add agent-session, log, tool-call, sandbox, command-execution, artifact,
  verification, and diff records.
- Implement the worker task handler, idempotency/lease strategy, cancellation
  signal, deadlines, retry policy, and cleanup supervisor.
- Stream persisted task events through SSE.
- Exit criterion: a deterministic fake agent can move a task through the state
  machine and leave a complete audit trail.

### Phase 3 — safe repository and sandbox execution

- Implement repository preparation: clone/fetch, immutable base commit,
  task-specific branch, status and diff collection.
- Implement a local Docker SandboxBackend plus a fake backend for tests.
- Enforce workspace path validation, command timeout, CPU/memory/PID limits,
  non-root execution, network policy, and guaranteed destroy-on-exit.
- Implement filesystem, command, and read-only Git tools using Pydantic input
  schemas and a policy gate.
- Exit criterion: a fixture repository can be safely modified and tested in a
  Docker sandbox; its diff and command outputs are persisted.

### Phase 4 — agent loop and model integration

- Implement provider-neutral model client and structured tool-call protocol.
- Add bounded context, iteration limits, tool result truncation/artifact
  fallback, invalid-call handling, and provider-failure behavior.
- Implement objective verification loop: test, lint, type-check, build, and
  custom commands; failed results are returned to the agent until a limit is
  reached.
- Exit criterion: using a configured provider, the agent completes a small
  fixture-repository task and reports objectively verified results.

### Phase 5 — user experience

- Build dashboard, project/repository management, task creation, task detail,
  streamed event timeline, verification display, logs, and diff review.
- Include terminal states, retry/cancel affordances, loading/error/empty
  states, and accessible responsive UI.
- Exit criterion: a user can perform and inspect the MVP flow without calling
  APIs manually.

### Phase 6 — hardening and operational readiness

- Threat-model review, sandbox escape testing, permission tests, secret
  handling, retention policies, quotas, rate limits, and dependency scanning.
- Add metrics, tracing, backups, alerting, runbooks, and failure-injection
  tests.
- Exit criterion: security requirements SR-001 through SR-011 and recovery
  behaviors are testable and documented.

## 7. Quality strategy

| Level | Focus |
| --- | --- |
| Unit | State transitions, authorization policy, workspace validation, tool schemas, and agent iteration rules. |
| Integration | Database migrations/repositories, queue dispatch, artifact storage, Git adapter, and Docker adapter. |
| Contract | API request/response schemas and model-provider/tool protocol adapters. |
| End-to-end | Fixture repository task: edit, test, verify, persist diff, and cleanup. |
| Security | Traversal attempts, dangerous mounts, secret non-exposure, denied tools, quota/timeout/cancellation cleanup. |

Every phase adds automated tests before its implementation is considered
complete. The fake sandbox and fake model make the agent workflow deterministic
in CI; Docker and real-provider tests run separately with explicit credentials.

## 8. Milestone-one implementation order

1. Bootstrap the source tree and local service definitions.
2. Add backend toolchain and health endpoint with tests.
3. Add typed configuration and structured logging.
4. Add domain task statuses and transition tests.
5. Add database base, migrations, and project/task vertical slice.
6. Add queue/worker and a deterministic execution simulation.

This order creates a tested control plane before any untrusted code is allowed
to run.

## 9. Decisions requiring confirmation before implementation

- Identity: local email/password for development only, or an existing identity
  provider to integrate from the start?
- Repository sources: local Git remotes only for MVP, or GitHub private
  repositories as an initial requirement?
- Model provider: which provider/model and billing/secret ownership model will
  be used for the first live-agent milestone?
- Deployment: is the target a single Linux server with Docker Compose, and can
  sandbox execution be placed on a separate host from the API/worker?
- Network policy: which package registries/Git hosts must restricted sandboxes
  access?
- Retention: how long should task logs, diffs, repository workspaces, and
  artifacts be retained?

Until these are answered, the scaffold uses interfaces and local-safe defaults
instead of hard-coding provider credentials or external integrations.
