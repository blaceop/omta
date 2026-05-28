# Mini AI Workflow Builder

A local-first AI workflow builder built for the Omniflow take-home exercise.

The app focuses on a small but complete execution loop rather than feature breadth. It supports authoring a multi-step workflow, executing it with real LLM calls, persisting workflow and run state, surfacing step-by-step status, and retrying failed steps.

The backend uses the OpenAI-compatible SDK interface, so it can talk to either:

- OpenAI directly
- Alibaba Cloud Bailian, by setting a custom API base URL and model

For a dedicated frontend/backend startup guide, see [RUNNING.md](/Users/guanby/Repos/omta/RUNNING.md).

## Current Implementation

The current codebase includes:

- a `React + Vite + TypeScript` frontend
- a `FastAPI + SQLite` backend
- workflow CRUD
- execution creation and persistence
- step-by-step execution state
- three step types:
  - `research`
  - `summarize`
  - `draft`
- tool-calling support for the `research` step
- one tool implementation: `http_fetch`
- failed-step retry
- near-real-time execution updates via frontend polling

## What The App Does

Users can:

- create a workflow
- edit its name, description, step order, prompts, and instructions
- run the workflow with an input prompt
- inspect each execution step's:
  - status
  - input
  - output
  - error
  - tool trace
- retry a failed step without recreating the whole execution

Example workflow:

1. Research a topic
2. Summarize the findings
3. Draft an email

## Tech Stack

### Frontend

- `React`
- `Vite`
- `TypeScript`
- `React Router`
- `TanStack Query`

### Backend

- `FastAPI`
- `SQLModel`
- `SQLite`
- `Pydantic`

### AI Integration

- `OpenAI Python SDK`
- OpenAI-compatible provider configuration

## Repository Structure

```text
backend/
  app/
    api/
    engine/
    llm/
    models/
    schemas/
    services/
    tools/
    utils/
  requirements.txt
frontend/
  src/
    api/
    components/
    hooks/
    pages/
    styles/
    types/
  package.json
README.md
DECISIONS.md
STACK_DECISION.md
SPEC_SCHEMA_AND_IMPLEMENTATION_PLAN.md
```

## Workflow Model

The workflow model is intentionally linear.

Each workflow contains an ordered list of steps. Each step stores:

- name
- type
- prompt template
- instructions
- optional model override
- tool-enabled flag

The three supported step types are:

### `research`

An LLM-powered agent step. It can invoke tools through the model tool-calling loop.

### `summarize`

A plain LLM step for condensing previous output.

### `draft`

A plain LLM step for turning prior output into a user-facing draft.

## Tool Calling

The `research` step is wired to a real tool loop.

The backend sends the step context and tool definitions to the model. If the model emits a tool call, the backend executes the tool, appends the tool result, and continues the loop until a final answer is produced or the step fails.

Current tool implementation:

- `http_fetch(url)`

The tool:

- fetches a URL
- strips markup into rough text
- truncates the response to a manageable size

## Execution Model

Each run creates:

- one `execution` row
- one `execution_step` row per workflow step

Each execution step tracks:

- `status`
- `input_text`
- `output_text`
- `error_message`
- `tool_calls_json`
- `attempt_count`

Execution statuses:

- `pending`
- `running`
- `succeeded`
- `failed`

The backend executes workflow steps sequentially in a background task. The frontend polls the execution detail endpoint once per second while a run is active.

## Retry Behavior

Failed steps can be retried.

Current retry behavior:

- the failed step is reset to `pending`
- all later steps are reset to `pending`
- the failed step's `attempt_count` increments
- the backend resumes execution from that step

This path has been manually verified in the current build.

## Local Setup

### Prerequisites

- `Python 3.11+`
- `Node.js 20+`
- `npm`
- an LLM API key if you want successful LLM execution

## Backend Setup

```bash
cd /Users/guanby/Repos/omta/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Update `backend/.env` with your real provider settings.

### Option 1: OpenAI

```bash
LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key
LLM_BASE_URL=
LLM_MODEL=gpt-4.1-mini
DATABASE_URL=sqlite:///./app.db
```

### Option 2: Alibaba Cloud Bailian

Fill in your Bailian key and your Bailian OpenAI-compatible endpoint URL.

```bash
LLM_PROVIDER=bailian
LLM_API_KEY=your_bailian_api_key
LLM_BASE_URL=your_bailian_openai_compatible_base_url
LLM_MODEL=your_bailian_model_name
DATABASE_URL=sqlite:///./app.db
```

If your Bailian account exposes an OpenAI-compatible endpoint, this app can use it without changing the execution logic because the backend client accepts a custom `base_url`.

The previous OpenAI-only variables are no longer used.

Use:

```bash
LLM_API_KEY=...
LLM_BASE_URL=...
LLM_MODEL=...
```

Start the backend:

```bash
cd /Users/guanby/Repos/omta/backend
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Backend URL:

[`http://localhost:8000`](http://localhost:8000)

## Frontend Setup

```bash
cd /Users/guanby/Repos/omta/frontend
npm install
npm run dev -- --host 127.0.0.1
```

Frontend URL:

[`http://127.0.0.1:5173`](http://127.0.0.1:5173)

## Verified Commands

These were run successfully during implementation:

### Frontend

```bash
cd /Users/guanby/Repos/omta/frontend
npm install
npm run build
npm run dev -- --host 127.0.0.1
```

### Backend

```bash
cd /Users/guanby/Repos/omta/backend
.venv/bin/pip install -r requirements.txt
python3 -m compileall app
.venv/bin/uvicorn app.main:app --port 8000
```

## Example API Flow

### Create workflow

`POST /api/workflows`

### List workflows

`GET /api/workflows`

### Create execution

`POST /api/workflows/{workflow_id}/executions`

### Poll execution detail

`GET /api/executions/{execution_id}`

### Retry failed step

`POST /api/executions/{execution_id}/steps/{execution_step_id}/retry`

## Successful Example Run

One verified successful run used this input:

```text
Research recent AI workflow builder trends and draft an internal summary email.
```

Workflow:

1. `research`
2. `summarize`
3. `draft`

Observed outcome from execution `#3`:

- `research` produced a structured internal summary of recent AI workflow builder trends
- `summarize` compressed that report into concise bullet points
- `draft` turned the summary into a polished internal email

Example highlights from the successful run:

- `research` identified themes such as no-code/low-code adoption, agentic workflows, multi-LLM integration, enterprise controls, observability, and human-in-the-loop patterns
- `summarize` reduced the longer report into actionable findings and recommendations
- `draft` generated a clear internal email with key findings and suggested next steps

This run was also useful because the `research` step encountered multiple imperfect tool results while still succeeding overall. Several fetch attempts returned failures such as:

- `403 Forbidden`
- `404 Not Found`
- `429 Too Many Requests`

The workflow still completed because tool failures are fed back into the agent loop rather than automatically crashing the entire step. That behavior is intentional and is part of the project's execution model.

## Manual Verification Notes

The following paths were manually exercised against the running backend:

- `GET /api/health`
- `POST /api/workflows`
- `GET /api/workflows`
- `POST /api/workflows/{id}/executions`
- `GET /api/workflows/{id}/executions`
- `GET /api/executions/{id}`
- `POST /api/executions/{id}/steps/{step_id}/retry`

Observed behavior:

- workflow creation succeeds
- workflow listing succeeds
- execution creation succeeds
- execution state is persisted
- failed step state is visible
- retry resets the failed step and increments `attempt_count`
- at least one full workflow execution completed successfully end-to-end

In the current environment, LLM execution fails unless valid provider credentials and connectivity are available. The failure path is still useful because it confirms that execution errors are surfaced and persisted correctly.

## Current Limitations

The current implementation intentionally does not include:

- graph-based workflow editing
- branching or loops
- authentication
- collaboration
- queue-backed worker infrastructure
- deployment configuration
- advanced tool sandboxing

## Related Docs

- [DECISIONS.md](/Users/guanby/Repos/omta/DECISIONS.md)
- [STACK_DECISION.md](/Users/guanby/Repos/omta/STACK_DECISION.md)
- [SPEC_SCHEMA_AND_IMPLEMENTATION_PLAN.md](/Users/guanby/Repos/omta/SPEC_SCHEMA_AND_IMPLEMENTATION_PLAN.md)
