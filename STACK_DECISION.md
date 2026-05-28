# Stack Decision: Option C (`React + FastAPI + SQLite`)

## Summary

For this assignment, I would use a split frontend/backend architecture:

- Frontend: `React + Vite + TypeScript`
- Backend: `FastAPI`
- Database: `SQLite`
- LLM integration: `OpenAI Python SDK`
- Execution updates: client-side polling

This stack is a deliberate choice for a small but real AI workflow system. The goal is not to build the most scalable platform possible, but to build a working product that makes execution state, step chaining, tool calling, and failure handling visible and understandable.

## Why This Stack Fits The Assignment

The assignment is evaluating judgment under constraints more than raw feature count. The core requirements are:

- define multi-step workflows
- execute them with real LLM calls
- persist workflows and execution state
- show which step is running and what each step produced
- support retries at the step level
- implement real tool calling inside the agent loop

`React + FastAPI + SQLite` fits those requirements well because it keeps the product shape simple while letting the agent runtime stay explicit.

## Why `React + Vite + TypeScript` For The Frontend

The frontend needs to do three things well:

- provide a usable workflow builder
- provide an execution details view with near-real-time updates
- make failures visible instead of hiding them behind a form

React is a strong fit because the UI is stateful but not unusually complex. The app needs editable forms, step lists, status indicators, and execution detail panels. That maps naturally to React components and local state.

Vite is a good choice because the project does not need framework-level rendering features. This is a locally run product exercise, not a content-heavy web app. Vite keeps startup and iteration fast and avoids introducing extra frontend architecture that is unrelated to the assignment.

TypeScript is useful here because the frontend is consuming structured workflow and execution data that changes over time. Shared API shapes are important in a system where execution state drives the UI.

## Why `FastAPI` For The Backend

FastAPI is the main reason to choose Option C over a pure JavaScript stack.

This project is not just CRUD. The interesting backend work is:

- modeling workflows and execution runs
- executing steps in order
- passing output from one step into the next
- handling retries
- integrating with an LLM
- running a tool-calling loop
- storing step-by-step execution results

Python is especially comfortable for that style of code. The execution engine, tool loop, and prompt orchestration are easier to express cleanly in Python than they often are in a more UI-centered full-stack framework.

FastAPI is a strong fit because it gives:

- clear REST APIs
- good request/response validation via Pydantic
- a straightforward async model
- low ceremony for a small service

That means more time can go into the parts the assignment actually cares about: execution semantics and AI integration.

## Why `SQLite`

The project needs durable storage, but not a large database setup. The required data model is relational and modest in scope:

- workflows
- workflow steps
- executions
- execution steps

SQLite is enough for this because the assignment is local, single-user, and low-concurrency. It keeps setup friction low while still providing proper persistence and relational modeling.

Choosing SQLite also reflects the assignment's instruction not to over-engineer. It keeps complexity focused on workflow execution rather than infrastructure.

## Why Polling Instead Of WebSockets

The product needs real-time or near-real-time execution feedback, but it does not need a full streaming architecture to prove the concept.

Polling is the best fit for this scope because it is:

- simple to implement
- easy to reason about
- reliable in a local dev environment
- sufficient for step-by-step updates

The user experience is still strong if the client refreshes execution state every second while a run is active.

## Why This Stack Is Strong For AI Integration

The assignment is specifically testing whether the system behaves like a real workflow runner rather than a form that calls an LLM once.

Option C supports that well because it separates concerns clearly:

- React handles editing workflows and visualizing progress
- FastAPI handles orchestration and execution state
- Python services handle LLM calls and tool loops
- SQLite stores both definitions and run history

That separation helps keep the AI logic legible. The agent loop is not hidden inside UI code or mixed into route handlers. It can live in backend modules like:

- `engine/runner.py`
- `engine/step_executor.py`
- `llm/tool_loop.py`
- `tools/registry.py`

This makes the system easier to explain in a walkthrough and easier to evolve later.

## Why Not A Single Full-Stack Framework

A single full-stack framework would also work for this assignment, especially for speed. I did not choose that route here because the most important technical differentiator in this project is the backend execution model, not the page framework.

Using a split frontend/backend setup makes the workflow runtime more explicit:

- the UI edits workflow definitions
- the API creates executions
- the backend runner updates state over time
- the frontend polls the execution record and renders progress

That is closer to how this type of system is reasoned about in production, even though the implementation here remains intentionally lightweight.

## Alternatives Considered

### Option A: `Next.js + Prisma + SQLite`

This is likely the fastest path to a polished assignment submission. It is a very reasonable choice if the goal is maximum delivery speed with minimal project setup.

I did not prioritize it here because the execution engine would likely live closer to the web app layer. That is fine for a small demo, but it makes the runtime less distinct than I want for this assignment.

### Option B: `React + Fastify + SQLite`

This would also be a solid split-architecture choice. The main difference is whether I want the backend to be expressed in Node or Python.

I prefer Python for this assignment because the agent execution logic, tool loop, and prompt orchestration are more naturally expressed there.

### Option D: queue/worker-based architecture

This would better resemble a production-grade execution system, but it would add setup cost and architectural weight that are not necessary for the assignment's goals.

It is a reasonable production direction, but not the best default for a constrained take-home exercise.

## What This Stack Optimizes For

This stack is optimized for:

- clear workflow execution semantics
- explicit AI orchestration code
- low infrastructure overhead
- fast local setup
- easy explanation in a demo

It is not optimized for:

- high concurrency
- multi-user collaboration
- distributed workers
- production-grade queueing
- deployment complexity

That tradeoff is intentional.

## Risks And Tradeoffs

This stack still has downsides:

- two runtimes to manage during development
- no shared language across frontend and backend
- polling is less elegant than streaming
- in-process execution is fine for a demo but not ideal for production

Those are acceptable tradeoffs for this assignment because they do not weaken the core evaluation areas. If anything, they keep the implementation focused on the most important product and runtime behaviors.

## What I Would Change In Production

If this were a production system, I would likely change three things first:

1. Replace in-process execution with a real job queue and worker model.
2. Replace SQLite with Postgres.
3. Add stronger execution observability, including structured event logs and better step-level traces.

Those changes would improve reliability and scalability, but they are intentionally deferred for the assignment version.

## Final Decision

I would choose Option C because it creates the best balance of:

- clear UI implementation
- explicit backend execution design
- natural Python-based AI orchestration
- low setup overhead
- strong explainability during review

For this assignment, that balance matters more than picking the fastest possible scaffolding or the most production-like infrastructure.
