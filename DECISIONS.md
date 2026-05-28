# DECISIONS

## What I Built

I built a deliberately scoped AI workflow builder with a linear execution model.

The current implementation includes:

- workflow creation and editing
- ordered multi-step workflows
- persisted workflow definitions in SQLite
- persisted execution history in SQLite
- per-step execution status
- per-step input, output, and error storage
- three step types:
  - `research`
  - `summarize`
  - `draft`
- tool calling for the `research` step
- one non-LLM tool implementation: `http_fetch`
- failed-step retry
- a frontend execution view with polling-based status refresh

The workflow is intentionally modeled as a sequence of steps rather than a graph. A representative flow is:

1. Research a topic
2. Summarize the findings
3. Draft an email

That scope keeps the runtime behavior concrete and inspectable:

- step order is explicit
- each step writes durable state
- outputs pass forward step by step
- tool calls happen inside the agent loop
- failed steps can be retried

## What I Cut And Why

I intentionally did not build:

- a visual node graph editor
- branches, loops, or arbitrary DAG execution
- auth or collaboration
- WebSockets or SSE
- a real queue/worker runtime
- multi-provider routing
- long-term memory or retrieval
- a large tool ecosystem

These were deliberate cuts.

The assignment is not asking for a complete agent platform. It is asking for a working system that reveals architectural judgment. I chose to spend time on the parts most directly tied to that evaluation:

- state modeling
- execution transparency
- retry semantics
- real LLM chaining
- real tool-calling behavior

I also chose polling over streaming because it was enough to satisfy near-real-time execution feedback without adding extra infrastructure. The polling model is simple, locally reliable, and easy to explain.

## Why I Chose This Architecture

I used:

- Frontend: `React + Vite + TypeScript`
- Backend: `FastAPI`
- Database: `SQLite`

I chose a split frontend/backend architecture because I wanted the execution engine to remain explicit as a backend concern instead of being folded into a full-stack web framework.

That separation maps cleanly to the product:

- the frontend edits workflow definitions and visualizes run state
- the backend owns persistence, orchestration, LLM calls, and tools

I chose Python on the backend because the execution engine, tool loop, and prompt orchestration are easier to express clearly there.

I chose SQLite because it matches the assignment scope:

- local
- single-user
- low-concurrency
- persistence required
- setup should stay lightweight

## One Architectural Decision I Would Change In Production

The biggest shortcut in the current implementation is that workflow execution runs inside the backend process through FastAPI background tasks.

That is the right tradeoff for this assignment because it minimizes setup cost and keeps the app easy to run locally. But it is not how I would want to scale the system.

In production, I would change three things quickly:

1. Move execution into a queue + worker model.
2. Replace SQLite with Postgres.
3. Add structured observability around prompts, tool calls, retries, and failure traces.

That would improve concurrency, reliability, and debuggability for longer-running or multi-user workloads.

## Where Current AI Agent Builders Break Down

### 1. They are black boxes

A common failure mode in agent builders is that users can start a run, but they cannot see:

- which step is running
- what input the step actually received
- what the model returned
- what tool was called
- why something failed

This project addresses that by treating execution as a first-class product surface. Each step stores and exposes:

- status
- input
- output
- error
- tool trace

### 2. They are optimized for the happy path only

Many demos feel impressive when everything succeeds and unusable when something breaks.

I wanted failure to be modeled rather than hidden. Each step is independently tracked, and the execution view shows failure at the exact step where it occurred. The retry path is also explicit instead of requiring a full rerun.

### 3. They mix prompting and orchestration too early

Another common failure mode is prompt spaghetti: UI configuration, prompt construction, execution semantics, and tool logic get mixed together.

I tried to separate those concerns:

- workflow definitions live in stored step configs
- execution sequencing lives in the runner
- step-type dispatch lives in the step executor
- tool calling lives in a dedicated loop

This is still a small system, but the boundaries are intentional.

### 4. They over-promise generality

Many workflow builders suggest arbitrary flexibility without strong semantics for state, retries, and partial reruns.

I intentionally chose a narrower workflow model. It is less flexible than a graph-based builder, but more honest:

- step chaining is real
- state transitions are durable
- failure is visible
- retry behavior is defined

## What I Intentionally Punted On

There are several important platform problems I intentionally did not solve here:

- prompt versioning
- model drift and deterministic replay
- tool sandboxing and trust
- multi-tenant isolation
- concurrent editing
- access control
- branching/loop semantics
- deployment and operations

I would rather show a constrained system with clear behavior than a broader system with fuzzy guarantees.

## How I Used AI Coding Tools

I used AI coding tools as implementation accelerators, not as substitutes for architectural judgment.

I used them for:

- scaffolding the project structure
- generating repetitive boilerplate
- drafting API and schema shapes
- iterating on UI components
- refining documentation

The core decisions I owned directly were:

- choosing the stack
- choosing a linear workflow model instead of a DAG
- defining the boundary between frontend, backend, runner, and tool loop
- deciding what to cut
- defining retry semantics and state transitions

In practice, I treated AI as a way to move faster on implementation details while keeping the system design decisions explicit and intentional.

## Honest Status Of The Current Build

The current implementation is working but intentionally lightweight.

What I verified directly:

- workflow CRUD works
- execution creation works
- execution state persists
- failed step state is visible in the API and UI
- retry resets and reruns the failed step
- frontend dev server starts
- frontend production build succeeds

The environment I tested in did not have working OpenAI connectivity, so the execution path currently demonstrates the failure path more than the successful LLM path. I consider that acceptable for development because it still validates the execution model, persistence, and retry behavior. With a valid key and working outbound connectivity, the same paths should produce successful LLM outputs.

## Final Tradeoff

This project is intentionally smaller than a modern no-code agent builder.

That is by design.

I prioritized:

- explicit state
- transparent execution
- real chaining
- tool-calling integration
- retry behavior

over:

- breadth of workflow features
- visual complexity
- infrastructure completeness

For this assignment, I believe that tradeoff shows more judgment than trying to build a broader but less reliable system.
