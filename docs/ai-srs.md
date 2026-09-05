# Software Requirements Specification (SRS)

## AI Coding Server

**Version:** 1.0  
**Status:** Draft  
**Project Type:** AI-powered software engineering platform  
**Primary Goal:** Enable an AI agent to autonomously perform software-development tasks inside isolated execution environments.

---

# 1. Introduction

## 1.1 Purpose

The **AI Coding Server** is a backend platform that allows an AI coding agent to work on real software repositories.

A user provides a programming task, such as:

> Add authentication to the API and make all existing tests pass.

The system provides the AI with controlled access to:

- repository files;
- code search;
- file modification;
- shell commands;
- Git;
- testing;
- build tools.

The AI performs the work inside an isolated **sandbox** rather than directly on the host machine.

The platform records the complete execution process, including tasks, agent sessions, model interactions, tool calls, sandbox executions, logs, verification results, and generated diffs.

---

# 2. Problem Statement

Existing AI coding tools can generate code, but a useful autonomous coding system needs to do considerably more.

The system must allow an AI agent to:

1. understand an existing repository;    
2. determine which files are relevant;
3. modify those files;
4. execute the modified software;
5. run tests;
6. inspect failures;
7. modify the implementation again;
8. verify the final result;
9. produce a reviewable Git diff.

This introduces several engineering problems:

- How does the AI interact with the repository?
- How are commands executed safely?
- How is the AI prevented from accessing the host?
- How are tasks scheduled?
- How are multiple agents isolated?
- How are tool calls recorded?
- How are model failures handled?
- How are changes reviewed?
- How are permissions enforced?
- How is the execution environment created and destroyed?

The AI Coding Server addresses these problems as one integrated platform.

---

# 3. Objectives

## 3.1 Primary Objectives

The system shall:

- execute AI coding tasks;
- provide controlled tools to AI agents;
- isolate code execution;
- manage Git repositories;
- run tests and verification;
- record agent activity;
- generate diffs;
- provide task status to users;
- enforce permissions and resource limits.

## 3.2 Secondary Objectives

The architecture should support future:

- GitHub integration;
- automatic pull requests;
- multiple AI models;.
- repository indexing;
- semantic code search;
- persistent project memory;
- distributed workers;
- multiple sandbox technologies.

---

# 4. Scope

## 4.1 Included

The first major version includes:

- authentication;
- user management;
- project management;
- repository management;
- task management;
- AI model management;
- model providers;
- agent sessions;
- tool system;
- sandbox management;
- shell execution;
- filesystem operations;
- Git operations;
- test execution;
- verification;
- diff generation;
- logs;
- artifacts;
- permissions;
- background workers;
- web dashboard.

## 4.2 Excluded From Initial Version

The following are intentionally deferred:

- Kubernetes-based execution;
- VM-level sandboxing;
- autonomous production deployment
- automatic merging;
- complex multi-agent collaboration;
- advanced repository embeddings;
- fully autonomous GitHub pull-request management;
- distributed multi-host execution.

---

# 5. Users and Actors

## 5.1 User

A user interacts with the platform through the frontend.

The user can:

- create projects;
- register repositories;
- create coding tasks;
- select models;
- monitor execution;
- cancel tasks;
- inspect logs;
- inspect diffs;
- approve repository operations.

## 5.2 AI Agent

The AI agent is responsible for solving a coding task.
It does not have unrestricted access to the infrastructure.
Instead, it operates through registered tools.

## 5.3 Model Provider

A service providing an AI model.

Examples include:

- hosted LLM APIs;
- self-hosted models;
- model gateways.

The system should not tightly couple the agent to a specific provider.

## 5.4 Worker

A background process that executes long-running tasks.

## 5.5 Sandbox Manager

Responsible for creating and controlling isolated execution environments.

---

# 6. System Overview

The platform consists of several major subsystems.

```text
                         USER
                           │
                           ▼
                    ┌─────────────┐
                    │   FRONTEND  │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ API SERVER  │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
       PostgreSQL       Task Queue       Auth
                           │
                           ▼
                    ┌─────────────┐
                    │    WORKER   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
            MODEL        TOOLS       SANDBOX
                                       │
                                       ▼
                                  REPOSITORY
                                       │
                                  ┌────┴────┐
                                  ▼         ▼
                                TESTS     BUILD
```

---

# 7. Functional Requirements

## FR-001 — Authentication

The system shall authenticate users before granting access to protected resources.

## FR-002 — Authorization

The system shall determine whether a user has permission to perform an operation.

Examples:

```text
project.read
project.write
task.create
task.cancel
repository.read
repository.write
agent.execute
git.push
git.create_pr
```

## FR-003 — Project Management

Users shall be able to create and manage projects.

A project shall contain:

- name;
- description;
- owner;
- default branch;
- repository association;
- project configuration.

## FR-004 — Repository Management

The system shall support:

- repository registration;
- cloning;
- fetching;
- branch inspection;
- branch creation;
- Git status;
- Git diff.

Later versions may support pushing and pull-request creation.

## FR-005 — Task Management

A user shall be able to create a task containing:

```text
title
description
project
repository
base branch
selected model
execution limits
verification configuration
```

## FR-006 — Task Scheduling

Tasks shall be placed into a queue before execution.

This prevents long-running AI tasks from blocking normal API requests.

## FR-007 — Agent Session

Each running task shall have an agent execution context containing:

- selected model;
- conversation;
- available tools;
- sandbox;
- iteration count;
- execution status;
- usage information.

## FR-008 — Tool Execution

The AI shall interact with the environment through predefined tools.

The platform shall validate tool requests before execution.

## FR-009 — File Operations

The agent shall be able to:

- list files;
- read files;
- search files;
- create files;
- modify files;
    
- apply patches.
    

## FR-010 — Command Execution

The agent shall be able to execute development commands inside the sandbox.

Examples:

```text
pytest
npm test
npm run build
npm install
go test ./...
cargo test
```

## FR-011 — Git Operations

The agent shall be able to inspect:

```text
git status
git diff
git branch
```

Later versions may allow:

```text
git commit
git push
```

## FR-012 — Test Execution

The system shall execute tests inside the sandbox and capture:

- command;
    
- exit code;
    
- stdout;
    
- stderr;
    
- execution time;
    
- timeout status.
    

## FR-013 — Verification

The system shall support objective verification through:

- tests;
    
- linting;
    
- type checking;
    
- builds;
    
- custom verification commands.
    

## FR-014 — Iterative Correction

If verification fails, the agent shall be able to inspect the failure and attempt another modification.

Example:

```text
Agent modifies code
       ↓
Tests fail
       ↓
Agent receives failure output
       ↓
Agent analyzes failure
       ↓
Agent modifies code
       ↓
Tests run again
```

## FR-015 — Diff Generation

After execution, the system shall calculate the Git diff between the original and modified repository state.

## FR-016 — Logs

The system shall record important execution events.

## FR-017 — Cancellation

Users shall be able to cancel active tasks.

Cancellation should:

1. mark the task as cancelled;
    
2. stop agent execution;
    
3. terminate active sandbox execution where possible;
    
4. clean up the sandbox.
    

## FR-018 — Timeouts

Tasks and individual commands shall have configurable time limits.

## FR-019 — Resource Limits

Sandbox execution shall have configurable:

- CPU;
    
- memory;
    
- process count;
    
- disk;
    
- execution duration.
    

## FR-020 — Artifacts

The system shall be able to store generated artifacts such as:

- test reports;
    
- build output;
    
- coverage reports;
    
- patches;
    
- large command output.
    

---

# 8. Agent Requirements

## 8.1 Agent Loop

The core agent loop shall operate approximately as follows:

```text
Load Task
   ↓
Load Repository
   ↓
Create Sandbox
   ↓
Initialize Context
   ↓
Send Context to Model
   ↓
Receive Model Response
   ↓
Tool Call?
 ┌───────┴────────┐
YES               NO
 │                 │
 ▼                 ▼
Validate        Determine
Tool             Result
 │
 ▼
Execute Tool
 │
 ▼
Record Result
 │
 ▼
Return Result
 │
 └──────► Model
```

## 8.2 Agent Termination

An agent shall terminate when:

- task is completed;
    
- verification succeeds;
    
- maximum iterations are reached;
    
- task timeout occurs;
    
- user cancels;
    
- model provider fails;
    
- sandbox fails;
    
- unrecoverable error occurs.
    

---

# 9. Tool System

The tool system forms the security boundary between the AI and the infrastructure.

## 9.1 Tool Definition

Every tool shall have:

```text
name
description
input schema
tool type
risk level
enabled status
```

Example:

```text
run_command

Input:
{
    command: string,
    working_directory: string,
    timeout: integer
}
```

## 9.2 Filesystem Tools

Initial tools:

```text
list_files()
read_file()
write_file()
search_files()
apply_patch()
```

## 9.3 Shell Tool

```text
run_command()
```

The shell tool must execute inside a sandbox.

## 9.4 Git Tools

```text
git_status()
git_diff()
git_branch()
git_create_branch()
```

Future:

```text
git_commit()
git_push()
```

## 9.5 Verification Tools

```text
run_tests()
run_linter()
run_type_checker()
run_build()
```

---

# 10. Sandbox Requirements

## 10.1 Purpose

The sandbox is the execution boundary for AI-generated code and commands.

The fundamental security principle is:

```text
AI controls the workspace.
AI does not control the host.
```

## 10.2 Sandbox Technology

The MVP shall use **Docker containers on Linux**.

A future implementation may support:

```text
Docker
Podman
VMs
Kubernetes
other isolation backends
```

The agent must interact with a generic Sandbox Manager rather than directly with Docker.

## 10.3 Sandbox Lifecycle

```text
CREATE
   ↓
INITIALIZE
   ↓
PREPARE WORKSPACE
   ↓
READY
   ↓
EXECUTE
   ↓
VERIFY
   ↓
COLLECT RESULTS
   ↓
STOP
   ↓
DESTROY
```

## 10.4 Sandbox Workspace

The repository shall exist within an isolated workspace such as:

```text
/workspace/repository
```

The agent's filesystem tools shall resolve paths relative to this workspace.

Attempts to access paths outside the workspace shall be rejected.

Example:

```text
../../etc/passwd
```

must not be permitted.

## 10.5 Container Security

The sandbox should use:

```text
non-root user
no privileged mode
restricted capabilities
no host PID namespace
no unnecessary host mounts
no Docker socket
no-new-privileges
seccomp
resource limits
network restrictions
execution timeouts
```

Docker's seccomp mechanism restricts system calls available to containers and provides an additional security boundary.

## 10.6 Host Filesystem

The sandbox must not receive arbitrary host filesystem mounts.

Especially prohibited by default:

```text
/
 /home
 /etc
 /var/run/docker.sock
```

The Docker socket must never be mounted into an untrusted coding sandbox because access to it can provide control over the Docker daemon.

## 10.7 Resource Limits

Each sandbox shall receive configurable limits:

```text
CPU
Memory
PIDs
Disk
Execution duration
```

Docker provides mechanisms for CPU, memory, and process constraints.

## 10.8 Network

Sandbox networking shall support:

```text
NONE
RESTRICTED
FULL
```

Default:

```text
RESTRICTED
```

or, for particularly untrusted tasks:

```text
NONE
```

Restricted networking may allow package registries and Git servers while blocking arbitrary destinations.

## 10.9 Secrets

The sandbox shall not automatically receive:

```text
database passwords
LLM API keys
host SSH keys
production environment variables
unrelated Git credentials
```

Secrets required for a specific operation must be explicitly authorized and narrowly scoped.

---

# 11. Sandbox Execution Flow

When the model requests:

```text
run_command("pytest")
```

the system shall perform:

```text
LLM
 │
 ▼
Tool Call
 │
 ▼
Tool Validation
 │
 ▼
Permission Check
 │
 ▼
Agent Worker
 │
 ▼
Sandbox Manager
 │
 ▼
Docker Container
 │
 ▼
pytest
 │
 ▼
stdout/stderr/exit code
 │
 ▼
Tool Result
 │
 ▼
Agent
```

The AI never directly executes commands on the API server.

---

# 12. Sandbox Manager Interface

The sandbox abstraction should provide operations similar to:

```text
create_sandbox(config)
start_sandbox(id)
execute(id, command)
get_status(id)
collect_artifact(id)
stop_sandbox(id)
destroy_sandbox(id)
```

The interface hides the underlying runtime.

For example:

```text
Agent
  ↓
Sandbox Manager
  ↓
DockerBackend
```

Later:

```text
Agent
  ↓
Sandbox Manager
  ↓
VMBackend
```

without changing the agent itself.

---

# 13. Database Requirements

PostgreSQL shall be the primary relational database.

## 13.1 Entity List

The initial database shall contain the following major entities:

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

---

# 14. Database Entity Specifications

## 14.1 User

Represents an authenticated platform user.

```text
users

id
email
name
status
created_at
updated_at
```

Relationships:

```text
User → Projects
User → Tasks
User → ProjectMembers
User → Logs
```

---

## 14.2 Project

Represents a logical software project.

```text
projects

id
owner_id
name
description
default_branch
created_at
updated_at
```

Relationships:

```text
Project
 ├── Repository
 ├── Tasks
 └── ProjectMembers
```

---

## 14.3 Project Member

Associates users with projects.

```text
project_members

id
project_id
user_id
role
created_at
```

Roles:

```text
owner
admin
developer
viewer
```

---

## 14.4 Repository

Represents a Git repository.

```text
repositories

id
project_id
provider
remote_url
default_branch
visibility
created_at
updated_at
```

Examples of providers:

```text
GitHub
GitLab
Bitbucket
self-hosted Git
```

---

## 14.5 Repository Credential

Represents credentials needed to access a private repository.

```text
repository_credentials

id
repository_id
credential_type
secret_reference
created_at
updated_at
```

Raw secrets should not be stored directly in ordinary application records.

---

## 14.6 Model Provider

Represents an AI model provider.

```text
model_providers

id
name
provider_type
endpoint
configuration
status
created_at
updated_at
```

---

## 14.7 Model

Represents a specific AI model.

```text
models

id
provider_id
name
model_identifier
context_window
capabilities
configuration
status
created_at
updated_at
```

Relationships:

```text
Model Provider
      │
      └── Models
             │
             └── Agent Sessions
```

---

## 14.8 Task

Represents the user's coding request.

```text
tasks

id
project_id
repository_id
created_by
selected_model_id
title
description
status
base_branch
agent_branch
max_iterations
timeout_seconds
created_at
started_at
completed_at
```

Statuses:

```text
queued
initializing
running
verifying
completed
failed
cancelled
timeout
```

---

## 14.9 Agent Session

Represents an AI execution session.

```text
agent_sessions

id
task_id
model_id
sandbox_id
status
iteration_count
input_tokens
output_tokens
started_at
ended_at
```

---

## 14.10 Message

Represents model/context communication.

```text
messages

id
agent_session_id
role
content
sequence_number
created_at
```

Roles:

```text
system
user
assistant
tool
```

Tool executions should also have their own structured records rather than relying entirely on message text.

---

## 14.11 Tool

Represents a capability available to the AI.

```text
tools

id
name
description
input_schema
tool_type
risk_level
enabled
created_at
updated_at
```

Examples:

```text
read_file
write_file
search_files
apply_patch
run_command
git_diff
git_commit
```

---

## 14.12 Tool Call

Represents one invocation of a tool.

```text
tool_calls

id
agent_session_id
tool_id
input
output
status
error
duration_ms
created_at
```

Statuses:

```text
requested
running
succeeded
failed
timeout
cancelled
denied
```

This entity is essential for auditing and debugging.

---

## 14.13 Sandbox

Represents an isolated execution environment.

```text
sandboxes

id
task_id
backend
runtime_id
image
status
workspace_path
cpu_limit
memory_limit
pid_limit
disk_limit
network_policy
created_at
started_at
destroyed_at
```

---

## 14.14 Sandbox Execution

Represents one command executed inside a sandbox.

```text
sandbox_executions

id
sandbox_id
tool_call_id
command
working_directory
exit_code
stdout_reference
stderr_reference
started_at
ended_at
timed_out
```

Large outputs should be stored externally and referenced rather than creating enormous database rows.

---

## 14.15 Verification Run

Represents objective verification.

```text
verification_runs

id
task_id
sandbox_id
type
command
status
exit_code
output_reference
started_at
ended_at
```

Types:

```text
test
lint
typecheck
build
custom
```

---

## 14.16 Diff

Represents modifications produced by a task.

```text
diffs

id
task_id
commit_id
base_commit
head_commit
patch_reference
files_changed
insertions
deletions
created_at
```

---

## 14.17 Artifact

Represents generated files or large outputs.

```text
artifacts

id
task_id
sandbox_id
artifact_type
storage_reference
size_bytes
checksum
created_at
```

Examples:

```text
test report
coverage report
build artifact
patch
large log
```

---

## 14.18 Log

Represents an auditable event.

```text
logs

id
user_id
task_id
agent_session_id
sandbox_id
level
event_type
message
metadata
created_at
```

Events may include:

```text
TASK_CREATED
TASK_STARTED
AGENT_STARTED
SANDBOX_CREATED
TOOL_STARTED
TOOL_COMPLETED
COMMAND_EXECUTED
TEST_FAILED
TEST_PASSED
TASK_COMPLETED
TASK_FAILED
TASK_CANCELLED
```

---

## 14.19 Permission

Represents an authorization capability.

```text
permissions

id
name
description
```

Examples:

```text
project.read
project.write
task.create
task.cancel
repository.read
repository.write
agent.execute
git.push
git.create_pr
```

---

# 15. Database Relationship Model

```text
                           USER
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
      PROJECT_MEMBER      TASK            LOG
             │              │
             ▼              │
          PROJECT           │
             │              │
       ┌─────┴─────┐        │
       ▼           ▼        │
 REPOSITORY      TASK ◄──────┘
       │           │
       ▼           ├───────────────┐
 CREDENTIALS       │               │
                   ▼               ▼
            AGENT_SESSION       SANDBOX
                   │               │
            ┌──────┴──────┐        ▼
            ▼             ▼   SANDBOX_EXECUTION
        MESSAGES      TOOL_CALL
                         │
                         ▼
                        TOOL

TASK
 ├── VERIFICATION_RUN
 ├── DIFF
 ├── ARTIFACT
 └── LOG

MODEL_PROVIDER
       │
       ▼
     MODEL
       │
       ▼
AGENT_SESSION
```

---

# 16. Task State Machine

```text
                  ┌──────────────┐
                  │    QUEUED    │
                  └──────┬───────┘
                         ▼
                  ┌──────────────┐
                  │ INITIALIZING │
                  └──────┬───────┘
                         ▼
                  ┌──────────────┐
             ┌───►│    RUNNING   │
             │    └──────┬───────┘
             │           │
             │           ▼
             │    ┌──────────────┐
             │    │  VERIFYING   │
             │    └──────┬───────┘
             │           │
             │      ┌────┴────┐
             │      │         │
             │      ▼         ▼
             │  COMPLETED   RUNNING
             │
             ├──────────────► FAILED
             │
             ├──────────────► CANCELLED
             │
             └──────────────► TIMEOUT
```

---

# 17. Security Requirements

## SR-001

AI-generated commands must never execute directly on the host application server.

## SR-002

Each task shall have an isolated workspace.

## SR-003

Sandbox processes shall operate with minimum required privileges.

## SR-004

The Docker socket shall not be exposed to coding sandboxes.

## SR-005

Host filesystem access shall not be exposed by default.

## SR-006

Resource limits shall be enforced.

## SR-007

Network access shall be configurable.

## SR-008

Secrets shall be isolated from ordinary sandbox execution.

## SR-009

Tool requests shall be validated before execution.

## SR-010

Sensitive operations such as Git push shall require appropriate authorization.

## SR-011

Security-relevant actions shall be logged.

---

# 18. Reliability Requirements

The system shall recover gracefully from:

```text
model API failure
network failure
tool failure
command failure
sandbox failure
worker failure
timeout
invalid model output
invalid tool arguments
```

A single failed command must not automatically destroy the entire task state.

---

# 19. Performance Requirements

The system should support multiple concurrent tasks subject to host resources.

The API should remain responsive while agents perform long-running operations.

Long-running work must therefore execute asynchronously through workers.

---

# 20. Frontend Requirements

## Dashboard

Display:

```text
active tasks
completed tasks
failed tasks
recent projects
agent activity
```

## Project Page

Display:

```text
repository
branch
project configuration
tasks
members
```

## Task Page

Display:

```text
task description
status
selected model
execution time
agent activity
tool calls
verification
```

## Diff Page

Display:

```text
changed files
insertions
deletions
patch
```

## Logs

Display:

```text
timestamp
event
tool
command
result
```

---

# 21. API Requirements

The backend should expose APIs conceptually similar to:

```text
POST   /auth/login

GET    /projects
POST   /projects
GET    /projects/{id}
PATCH  /projects/{id}
DELETE /projects/{id}

GET    /repositories
POST   /repositories
GET    /repositories/{id}

GET    /tasks
POST   /tasks
GET    /tasks/{id}
POST   /tasks/{id}/cancel

GET    /tasks/{id}/logs
GET    /tasks/{id}/tool-calls
GET    /tasks/{id}/diff
GET    /tasks/{id}/verification

GET    /models
GET    /tools
```

Exact API contracts belong in a separate API specification.

---

# 22. Background Worker Architecture

```text
                  API
                   │
                   ▼
              Task Queue
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
     Worker 1   Worker 2   Worker 3
        │
        ▼
   Agent Runtime
        │
   ┌────┼─────┐
   ▼    ▼     ▼
 Model Tools Sandbox
```

The worker owns the long-running agent loop.

The API should not remain connected to the agent for the entire task duration.

---

# 23. Complete Task Execution Sequence

```text
1. User creates task
        ↓
2. API validates request
        ↓
3. Task stored in PostgreSQL
        ↓
4. Task placed in queue
        ↓
5. Worker receives task
        ↓
6. Permission checks
        ↓
7. Sandbox created
        ↓
8. Repository prepared
        ↓
9. Agent session created
        ↓
10. Model receives task/context
        ↓
11. Model requests tools
        ↓
12. Tools execute in sandbox
        ↓
13. Results returned to model
        ↓
14. Agent modifies code
        ↓
15. Verification executes
        ↓
16. Failures returned to agent
        ↓
17. Agent iterates
        ↓
18. Verification succeeds
        ↓
19. Git diff generated
        ↓
20. Results persisted
        ↓
21. Sandbox destroyed
        ↓
22. Task marked completed
```

---

# 24. Example Scenario

User submits:

```text
Add pagination to GET /users.
Maintain backwards compatibility.
Add tests.
```

The agent might execute:

```text
list_files()
```

then:

```text
search_files("users")
```

then:

```text
read_file("app/routes/users.py")
```

then modify the implementation:

```text
apply_patch(...)
```

then:

```text
run_command("pytest")
```

Suppose:

```text
5 passed
2 failed
```

The failure output becomes input to the next agent iteration.

The agent modifies the implementation and runs:

```text
run_command("pytest")
```

Again:

```text
7 passed
```

The system then performs:

```text
run_linter()
run_type_checker()
git_diff()
```

and stores the results.

---

# 25. Technology Stack

## Frontend

```text
React
TypeScript
Vite
```

## Backend

```text
Python
FastAPI
Pydantic
SQLAlchemy
```

## Database

```text
PostgreSQL
```

## Queue

```text
Redis
Celery/RQ/custom worker
```

## AI

```text
LLM API/SDK
structured tool calling
```

## Sandbox

```text
Linux
Docker
namespaces
cgroups
seccomp
```

## Version Control

```text
Git
```

## Future Infrastructure

```text
GitHub API
Object storage
Monitoring
Distributed workers
VM sandboxing
```

---

# 26. Deployment Architecture

The first deployment can run on one Linux server:

```text
                    INTERNET
                       │
                       ▼
                  Reverse Proxy
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
         Frontend              API
                                  │
                     ┌────────────┼────────────┐
                     ▼            ▼            ▼
                 PostgreSQL     Redis        Worker
                                                │
                                                ▼
                                             Docker
                                                │
                                      ┌─────────┼─────────┐
                                      ▼         ▼         ▼
                                   Sandbox   Sandbox   Sandbox
```

The important distinction is that the API/worker host and the sandbox execution layer have different trust responsibilities.

---

# 27. Future Distributed Architecture

As workload increases:

```text
                     Load Balancer
                           │
                  ┌────────┴────────┐
                  ▼                 ▼
               API 1              API 2
                  │                 │
                  └────────┬────────┘
                           ▼
                       PostgreSQL
                           │
                         Redis
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Worker 1      Worker 2      Worker 3
             │             │             │
             ▼             ▼             ▼
         Sandbox Host  Sandbox Host  Sandbox Host
```

The Sandbox Manager abstracts away which host actually executes a task.

---

# 28. Development Phases

## Phase 1 — Agent Prototype

Implement:

```text
LLM
agent loop
tool calling
local repository
```

No frontend.

## Phase 2 — Sandbox

Implement:

```text
Docker sandbox
workspace
command execution
resource limits
timeouts
lifecycle management
```

## Phase 3 — Git

Implement:

```text
clone
branch
status
diff
```

## Phase 4 — Backend

Implement:

```text
FastAPI
PostgreSQL
authentication
tasks
worker
```

## Phase 5 — Frontend

Implement:

```text
projects
tasks
agent activity
logs
diff viewer
```

## Phase 6 — Verification

Implement:

```text
tests
lint
type checking
build
```

## Phase 7 — Security Hardening

Implement:

```text
permissions
network policies
secret isolation
resource quotas
audit logging
sandbox hardening
```

## Phase 8 — GitHub Integration

Implement:

```text
GitHub authentication
branch push
pull requests
issue → task
```

---

# 29. Key Design Principles

### Principle 1 — The Model Is Not the System

The LLM is only the reasoning engine.

```text
LLM
+
Tools
+
Agent Loop
+
Sandbox
+
Repository
+
Verification
+
Orchestration
=
AI Coding Server
```

### Principle 2 — Never Trust Agent-Generated Code

The code produced by the AI must be treated as potentially unsafe.

### Principle 3 — Execution Is Separate From Control

```text
CONTROL PLANE
API
Database
Auth
Queue
Permissions
Secrets

        TRUST BOUNDARY

EXECUTION PLANE
Sandbox
Repository
Generated code
Shell
Tests
Dependencies
```

### Principle 4 — Verification Must Be Objective

The AI saying:

```text
"the task is complete"
```

is not sufficient.

The platform should determine completion using actual tests, builds, linting, type checks, and other verification.

### Principle 5 — Everything Important Is Auditable

A completed task should allow the system to answer:

```text
Who created it?
Which repository was used?
Which model ran?
What did the agent request?
Which tools were called?
Which commands ran?
Where did they run?
What changed?
Which tests passed?
Which tests failed?
What was the final diff?
```

---

# 30. Acceptance Criteria

The MVP shall be considered functional when the following scenario works end-to-end:

```text
User
 ↓
Creates project
 ↓
Connects repository
 ↓
Creates coding task
 ↓
Task enters queue
 ↓
Worker starts
 ↓
Sandbox is created
 ↓
Repository is prepared
 ↓
AI agent starts
 ↓
Agent reads files
 ↓
Agent modifies files
 ↓
Agent runs tests
 ↓
Agent observes results
 ↓
Agent fixes failures
 ↓
Tests pass
 ↓
Git diff is generated
 ↓
Logs and verification results are stored
 ↓
Sandbox is destroyed
 ↓
User can inspect the final task and diff
```

The first implementation does **not** need to be a full autonomous software-development platform. It needs to establish the fundamental architecture correctly:

```text
             TASK
               │
               ▼
             AGENT
               │
               ▼
             TOOLS
               │
               ▼
            SANDBOX
               │
               ▼
          REPOSITORY
               │
               ▼
        TEST / VERIFY
               │
               ▼
             DIFF
```

That is the core of the AI Coding Server.