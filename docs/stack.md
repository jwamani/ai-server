# AI Coding Server — Technology Stack & Architecture Summary

## 1. Project Overview

The AI Coding Server is a platform that allows an AI coding agent to work on real software repositories. A user submits a programming task, the agent inspects and modifies the repository, executes development commands and tests inside an isolated sandbox, iterates on failures, and produces a reviewable Git diff.

**Core principle:** The AI controls the workspace, but it does not directly control the host system.

## 2. High-Level Architecture

```text
Frontend
   |
   | HTTP / WebSocket
   v
FastAPI API
   |
   +------------------+------------------+
   |                  |                  |
PostgreSQL          Redis             Auth
   |                  |
   |                  v
   |             Task Queue
   |                  |
   |                  v
   |             Celery Worker
   |                  |
   |          +-------+-------+
   |          |               |
   |      Agent Engine   Sandbox Manager
   |          |               |
   |          v               v
   |       LLM/API          Docker
   |          |               |
   |          v               v
   |       Tool System    Repository
   |                          |
   |                    Tests / Build
   |
   +---- Tasks / Logs / Diffs / Artifacts
```

## 3. Recommended Technology Stack

| Key Part | Technology | Purpose |
|---|---|---|
| Frontend | React + TypeScript + Vite | Dashboard, projects, tasks, agent activity and diffs |
| UI | Tailwind CSS | Styling |
| API Server | FastAPI + Python | REST API and application control |
| Validation | Pydantic | Request/response and configuration validation |
| ORM | SQLAlchemy 2 | Database access |
| Database | PostgreSQL | Durable application state |
| Migrations | Alembic | Database schema migrations |
| Authentication | JWT + OAuth2 | Authentication and authorization |
| Task Queue | Redis + Celery | Asynchronous long-running tasks |
| Agent Worker | Python | Runs the AI agent loop |
| LLM Integration | Model provider SDK/API | Model reasoning and tool calling |
| Agent Framework | Custom Python agent layer | Agent loop, state, context, tools and verification |
| Tool System | Python + Pydantic/JSON Schema | Controlled AI capabilities |
| Sandbox | Docker on Linux | Isolated code execution |
| Sandbox API | Docker Engine API / Python Docker SDK | Container lifecycle and execution |
| OS Isolation | Linux namespaces + cgroups | Process and resource isolation |
| Sandbox Security | seccomp + Linux capabilities + no-new-privileges | Reduce sandbox attack surface |
| Version Control | Git | Repository management and diffs |
| Git Integration | Git CLI initially | Clone, branch, status, diff and later commit/push |
| Artifact Storage | S3-compatible storage / MinIO | Large logs, patches, reports and artifacts |
| Realtime | WebSockets or Server-Sent Events | Live task and agent updates |
| Logging | Structured Python logging | Application and execution logs |
| Monitoring | Prometheus + Grafana | Metrics and infrastructure monitoring |
| Tracing | OpenTelemetry | Distributed tracing |
| Reverse Proxy | Nginx or Caddy | TLS and routing |
| Deployment | Docker Compose initially | Run platform services |
| Testing | Pytest + Vitest | Backend and frontend tests |
| CI/CD | GitHub Actions | Automated testing, builds and deployment |

## 4. Backend

The central backend uses **Python + FastAPI**. It handles authentication, authorization, projects, repositories, tasks, model configuration, permissions, agent control, task status, logs, diffs, and verification results.

Long-running coding tasks should not execute inside normal HTTP requests. They are placed into a queue and handled by background workers.

## 5. AI Agent

The agent should be a custom Python subsystem.

```text
Agent Engine
├── Context Manager
├── Model Client
├── Tool Registry
├── Tool Executor
├── State Manager
├── Iteration Controller
└── Verification Controller
```

### Agent Loop

```text
Task
  |
  v
Load repository/context
  |
  v
Send context to model
  |
  v
Model response
  |
  +---- No tool call ----> Continue / finish
  |
  +---- Tool call
          |
          v
     Validate tool
          |
          v
     Check permission
          |
          v
     Execute tool
          |
          v
     Return result
          |
          v
        Model
```

The model provides reasoning; the agent system controls what the model can actually do.

## 6. LLM Layer

The system should not be permanently coupled to one AI provider. Use a provider abstraction so multiple hosted or self-hosted models can be supported.

```python
class ModelProvider:
    async def generate(...):
        ...

    async def stream(...):
        ...
```

Potential providers include OpenAI, Anthropic, OpenRouter, self-hosted models, and other compatible providers.

## 7. Tool System

The AI interacts with the environment through controlled tools.

Initial tools:

```text
read_file
write_file
list_files
search_files
apply_patch

run_command

git_status
git_diff
git_branch

run_tests
run_linter
run_type_checker
run_build
```

The flow is:

```text
LLM
 |
 v
Tool Registry
 |
 v
Permission Check
 |
 v
Input Validation
 |
 v
Tool Executor
 |
 v
Sandbox
```

The model must never receive unrestricted host shell access.

## 8. Sandbox

The sandbox is one of the most important components. AI-generated code and commands must execute inside an isolated environment rather than directly on the API/worker host.

### Recommended MVP Technology

**Docker containers running on Linux.**

```text
Worker
  |
  v
Sandbox Manager
  |
  v
Docker
  |
  +-- Container
       |
       +-- /workspace/repository
       +-- Development runtime
       +-- Git
       +-- Tests
```

### Sandbox Lifecycle

```text
CREATE
  |
  v
INITIALIZE
  |
  v
PREPARE WORKSPACE
  |
  v
READY
  |
  v
EXECUTE
  |
  v
VERIFY
  |
  v
COLLECT RESULTS
  |
  v
STOP
  |
  v
DESTROY
```

### Sandbox Security

The sandbox should use:

- non-root execution;
- restricted Linux capabilities;
- no privileged mode;
- no Docker socket;
- no unnecessary host filesystem mounts;
- `no-new-privileges`;
- seccomp;
- CPU limits;
- memory limits;
- process/PID limits;
- disk limits;
- execution timeouts;
- configurable network access.

The sandbox should not automatically receive production credentials, database passwords, host SSH keys, LLM API keys, or unrelated environment variables.

### Network Policies

Support at least:

```text
NONE
RESTRICTED
FULL
```

The default should be restrictive.

## 9. Linux Isolation Technologies

Docker is the container technology, while Linux provides important underlying isolation mechanisms.

- **Namespaces:** isolate processes, filesystem views, networking, and users.
- **cgroups:** control CPU, memory, process counts, and other resources.
- **seccomp:** restrict system calls available to processes.
- **Linux capabilities:** reduce privileges available inside containers.
- **no-new-privileges:** prevents processes from gaining additional privileges.

These mechanisms form multiple security layers around sandbox execution.

## 10. Database

Use **PostgreSQL** as the primary relational database, with SQLAlchemy 2 and Alembic.

### Main Entities

```text
users
projects
project_members

repositories
repository_credentials

model_providers
models

tasks
agent_sessions
messages

tools
tool_calls

sandboxes
sandbox_executions

verification_runs
diffs
artifacts
logs

permissions
```

### Core Relationships

```text
User
 └── Project
      ├── Project Members
      ├── Repository
      │    └── Repository Credentials
      │
      └── Tasks
           ├── Agent Session
           │    ├── Messages
           │    └── Tool Calls
           │         └── Tool
           │
           ├── Sandbox
           │    └── Sandbox Executions
           │
           ├── Verification Runs
           ├── Diff
           ├── Artifacts
           └── Logs

Model Provider
 └── Models
      └── Agent Sessions
```

## 11. Redis and Celery

Coding tasks can take several minutes, so they should not run inside normal HTTP requests.

```text
POST /tasks
     |
     v
FastAPI
     |
     +--> PostgreSQL
     |
     +--> Redis
            |
            v
       Celery Worker
            |
            v
       Agent Runtime
```

The API returns a task ID while the worker performs the actual coding operation.

## 12. Git

Git is the repository foundation.

```text
Repository
    |
    v
Clone
    |
    v
Create agent branch
    |
    v
Agent modifies files
    |
    v
Run tests
    |
    v
Generate git diff
    |
    v
User reviews changes
```

Initially, the Git CLI is sufficient. Future GitHub integration can add repository access, branches, commits, pushes, pull requests, and issues.

## 13. Artifact Storage

Large outputs should not all be stored directly in PostgreSQL. Store large logs, patches, reports, and generated files in S3-compatible object storage such as MinIO, while PostgreSQL stores metadata and storage references.

## 14. Realtime Updates

Use WebSockets or Server-Sent Events for live task updates, such as:

```text
Agent started
      ↓
Reading app/main.py
      ↓
Searching for authentication
      ↓
Editing auth.py
      ↓
Running pytest
      ↓
Tests failed
      ↓
Fixing implementation
      ↓
Tests passed
```

## 15. Observability

For production use:

```text
Prometheus
    ↓
Metrics

Grafana
    ↓
Dashboards

OpenTelemetry
    ↓
Distributed traces
```

This makes it possible to determine where time is being spent, for example:

```text
LLM request       8 sec
Sandbox creation  4 sec
pytest           63 sec
Database          1 sec
```

## 16. Frontend

Recommended stack:

```text
React
TypeScript
Vite
Tailwind CSS
```

Main UI:

```text
Dashboard
├── Projects
├── Repositories
├── Tasks
│    └── Task Details
│         ├── Agent Activity
│         ├── Tool Calls
│         ├── Terminal Output
│         ├── Tests
│         ├── Logs
│         └── Diff
└── Settings
     ├── Models
     ├── Providers
     └── Permissions
```

## 17. Initial Deployment

Kubernetes is unnecessary for the first version. Use Docker Compose on a Linux server.

```text
Linux Server
    |
    v
Docker Compose
    |
    +-- FastAPI
    +-- React
    +-- PostgreSQL
    +-- Redis
    +-- Celery Worker
    +-- Docker Sandbox Runtime
```

Nginx or Caddy can handle TLS and routing.

## 18. Future Distributed Architecture

As the system grows:

```text
Load Balancer
      |
      +-- API 1
      +-- API 2
      |
      +-- PostgreSQL
      |
      +-- Redis
             |
       +-----+-----+-----+
       |           |     |
    Worker 1    Worker 2 Worker 3
       |           |     |
    Sandbox     Sandbox Sandbox
      Host        Host    Host
```

The Sandbox Manager should abstract the execution backend so Docker can later be supplemented or replaced by VM-based isolation.

## 19. Development Phases

### Phase 1 — Agent Prototype

- LLM integration
- agent loop
- tool calling
- local repository interaction

### Phase 2 — Sandbox

- Docker sandbox
- workspace
- command execution
- timeouts
- resource limits
- lifecycle management

### Phase 3 — Git

- clone
- branches
- status
- diff

### Phase 4 — Backend

- FastAPI
- PostgreSQL
- authentication
- task system
- worker
- queue

### Phase 5 — Frontend

- projects
- tasks
- agent activity
- logs
- diff viewer

### Phase 6 — Verification

- tests
- linting
- type checking
- builds

### Phase 7 — Security Hardening

- permissions
- network policies
- secret isolation
- resource quotas
- audit logging
- sandbox hardening

### Phase 8 — GitHub Integration

- GitHub authentication
- branch push
- pull requests
- issue-to-task workflows

## 20. Most Important Technologies to Master

### Tier 1 — Core Platform

```text
Python
FastAPI
PostgreSQL
SQLAlchemy
Redis
Celery
Docker
Git
React
TypeScript
```

### Tier 2 — AI Agent

```text
LLM APIs
Structured tool calling
JSON Schema
Agent loops
Context management
Streaming
```

### Tier 3 — Sandbox and Security

```text
Linux namespaces
cgroups
seccomp
Linux capabilities
Container security
Network isolation
Resource quotas
```

### Tier 4 — Production Infrastructure

```text
Nginx/Caddy
Prometheus
Grafana
OpenTelemetry
S3/MinIO
GitHub API
CI/CD
```

## 21. Core Architecture to Focus On

The three most important subsystems are:

```text
        Agent Loop
            |
            v
        Tool System
            |
            v
       Sandbox Manager
            |
            v
        Docker/Linux
```

The fundamental execution model is:

```text
                 TASK
                   |
                   v
                 AGENT
                   |
                   v
                 TOOLS
                   |
                   v
                SANDBOX
                   |
                   v
              REPOSITORY
                   |
                   v
             TEST / VERIFY
                   |
                   v
                 DIFF
```
