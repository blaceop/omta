# Schema And Implementation Plan

This document expands the Option C blueprint into:

- database schema
- Pydantic model drafts
- execution engine contracts
- a front-end and back-end file-by-file implementation plan

The goal is to make the project concrete enough that implementation can begin immediately.

## 1. Database Schema

The schema is intentionally narrow and relational. It separates workflow definitions from execution history.

### Table: `workflows`

Purpose:
- stores the editable definition of a workflow

Suggested columns:

```sql
CREATE TABLE workflows (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Notes:
- `name` is user-facing
- `description` is optional and mainly useful for list/detail views

### Table: `workflow_steps`

Purpose:
- stores ordered step definitions for a workflow

Suggested columns:

```sql
CREATE TABLE workflow_steps (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workflow_id INTEGER NOT NULL,
  position INTEGER NOT NULL,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  prompt_template TEXT NOT NULL,
  instructions TEXT,
  model TEXT,
  tool_enabled BOOLEAN NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
);
```

Constraints to enforce at the app layer:
- `type` must be one of:
  - `research`
  - `summarize`
  - `draft`
- `position` should be unique per workflow

Recommended index:

```sql
CREATE UNIQUE INDEX idx_workflow_steps_workflow_position
ON workflow_steps(workflow_id, position);
```

### Table: `executions`

Purpose:
- stores one workflow run

Suggested columns:

```sql
CREATE TABLE executions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workflow_id INTEGER NOT NULL,
  status TEXT NOT NULL,
  input_text TEXT NOT NULL,
  current_step_position INTEGER,
  error_message TEXT,
  started_at DATETIME,
  finished_at DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
);
```

Allowed `status` values:
- `pending`
- `running`
- `succeeded`
- `failed`

### Table: `execution_steps`

Purpose:
- stores per-step runtime state for a specific execution

Suggested columns:

```sql
CREATE TABLE execution_steps (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  execution_id INTEGER NOT NULL,
  workflow_step_id INTEGER NOT NULL,
  position INTEGER NOT NULL,
  name_snapshot TEXT NOT NULL,
  type_snapshot TEXT NOT NULL,
  status TEXT NOT NULL,
  input_text TEXT,
  output_text TEXT,
  error_message TEXT,
  tool_calls_json TEXT,
  attempt_count INTEGER NOT NULL DEFAULT 1,
  started_at DATETIME,
  finished_at DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE,
  FOREIGN KEY (workflow_step_id) REFERENCES workflow_steps(id) ON DELETE CASCADE
);
```

Allowed `status` values:
- `pending`
- `running`
- `succeeded`
- `failed`

Recommended index:

```sql
CREATE INDEX idx_execution_steps_execution_position
ON execution_steps(execution_id, position);
```

### Why snapshots exist in `execution_steps`

`name_snapshot` and `type_snapshot` are stored so execution history remains understandable even if the workflow is edited later.

This is a small but important decision. It prevents historical runs from becoming ambiguous after workflow changes.

## 2. ORM Model Draft

This can be implemented with either SQLModel or SQLAlchemy 2.0 plus Pydantic. The structure below is written in a SQLModel-friendly style.

## `backend/app/models/workflow.py`

Core enums:

```python
from enum import Enum


class StepType(str, Enum):
    RESEARCH = "research"
    SUMMARIZE = "summarize"
    DRAFT = "draft"
```

Workflow model draft:

```python
class Workflow(SQLModel, table=True):
    __tablename__ = "workflows"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    steps: list["WorkflowStep"] = Relationship(
        back_populates="workflow",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
```

Workflow step model draft:

```python
class WorkflowStep(SQLModel, table=True):
    __tablename__ = "workflow_steps"

    id: int | None = Field(default=None, primary_key=True)
    workflow_id: int = Field(foreign_key="workflows.id")
    position: int
    name: str
    type: StepType
    prompt_template: str
    instructions: str | None = None
    model: str | None = None
    tool_enabled: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    workflow: "Workflow" = Relationship(back_populates="steps")
```

## `backend/app/models/execution.py`

Execution enums:

```python
class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
```

Execution model draft:

```python
class Execution(SQLModel, table=True):
    __tablename__ = "executions"

    id: int | None = Field(default=None, primary_key=True)
    workflow_id: int = Field(foreign_key="workflows.id")
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING)
    input_text: str
    current_step_position: int | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    steps: list["ExecutionStep"] = Relationship(
        back_populates="execution",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
```

Execution step model draft:

```python
class ExecutionStep(SQLModel, table=True):
    __tablename__ = "execution_steps"

    id: int | None = Field(default=None, primary_key=True)
    execution_id: int = Field(foreign_key="executions.id")
    workflow_step_id: int = Field(foreign_key="workflow_steps.id")
    position: int
    name_snapshot: str
    type_snapshot: StepType
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING)
    input_text: str | None = None
    output_text: str | None = None
    error_message: str | None = None
    tool_calls_json: str | None = None
    attempt_count: int = 1
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    execution: "Execution" = Relationship(back_populates="steps")
```

## 3. Pydantic Schema Draft

These response/request models should stay separate from ORM models so the API remains stable and explicit.

## `backend/app/schemas/common.py`

```python
from enum import Enum


class StepType(str, Enum):
    research = "research"
    summarize = "summarize"
    draft = "draft"


class ExecutionStatus(str, Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
```

## `backend/app/schemas/workflow.py`

```python
class WorkflowStepBase(BaseModel):
    name: str
    type: StepType
    prompt_template: str
    instructions: str | None = None
    model: str | None = None
    tool_enabled: bool = False
```

```python
class WorkflowStepCreate(WorkflowStepBase):
    position: int
```

```python
class WorkflowStepUpdate(WorkflowStepBase):
    id: int | None = None
    position: int
```

```python
class WorkflowCreate(BaseModel):
    name: str
    description: str | None = None
    steps: list[WorkflowStepCreate]
```

```python
class WorkflowUpdate(BaseModel):
    name: str
    description: str | None = None
    steps: list[WorkflowStepUpdate]
```

```python
class WorkflowStepResponse(WorkflowStepBase):
    id: int
    workflow_id: int
    position: int
    created_at: datetime
    updated_at: datetime
```

```python
class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    steps: list[WorkflowStepResponse]
```

```python
class WorkflowListItem(BaseModel):
    id: int
    name: str
    description: str | None
    step_count: int
    updated_at: datetime
```

## `backend/app/schemas/execution.py`

Tool trace model draft:

```python
class ToolCallTrace(BaseModel):
    tool: str
    arguments: dict[str, Any]
    result_preview: str
```

Execution create:

```python
class ExecutionCreate(BaseModel):
    input_text: str
```

Execution step response:

```python
class ExecutionStepResponse(BaseModel):
    id: int
    execution_id: int
    workflow_step_id: int
    position: int
    name_snapshot: str
    type_snapshot: StepType
    status: ExecutionStatus
    input_text: str | None
    output_text: str | None
    error_message: str | None
    tool_calls: list[ToolCallTrace] = []
    attempt_count: int
    started_at: datetime | None
    finished_at: datetime | None
```

Execution response:

```python
class ExecutionResponse(BaseModel):
    id: int
    workflow_id: int
    status: ExecutionStatus
    input_text: str
    current_step_position: int | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    steps: list[ExecutionStepResponse]
```

Execution list item:

```python
class ExecutionListItem(BaseModel):
    id: int
    workflow_id: int
    status: ExecutionStatus
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
```

Retry request:

```python
class RetryExecutionStepRequest(BaseModel):
    pass
```

This request body can remain empty for MVP and still keep the route extensible.

## 4. Service Contracts

These are the key service boundaries the implementation should respect.

## `backend/app/services/workflow_service.py`

Responsibilities:
- create workflow
- list workflows
- get workflow detail
- update workflow
- replace step definitions in a controlled way

Suggested method signatures:

```python
def list_workflows(session: Session) -> list[WorkflowListItem]: ...
def create_workflow(session: Session, payload: WorkflowCreate) -> Workflow: ...
def get_workflow(session: Session, workflow_id: int) -> Workflow: ...
def update_workflow(session: Session, workflow_id: int, payload: WorkflowUpdate) -> Workflow: ...
```

Implementation notes:
- on update, replace steps wholesale rather than diffing in MVP
- validate positions are continuous and unique

## `backend/app/services/execution_service.py`

Responsibilities:
- create execution records
- create execution step snapshots from workflow steps
- load execution detail
- retry failed steps

Suggested method signatures:

```python
def create_execution(session: Session, workflow_id: int, payload: ExecutionCreate) -> Execution: ...
def get_execution(session: Session, execution_id: int) -> Execution: ...
def list_workflow_executions(session: Session, workflow_id: int) -> list[Execution]: ...
def retry_execution_step(session: Session, execution_id: int, execution_step_id: int) -> Execution: ...
```

Implementation notes:
- execution creation should snapshot workflow steps immediately
- retry should only allow failed steps
- retry should reset this step and later steps to `pending`

## 5. Execution Engine Contracts

## `backend/app/engine/context_builder.py`

Purpose:
- construct the prompt input for the current step

Suggested output structure:

```python
class StepExecutionContext(BaseModel):
    original_input: str
    previous_outputs: list[dict[str, str]]
    current_input: str
```

Rules:
- first step receives `execution.input_text`
- later steps receive previous successful step output as `current_input`
- include prior step outputs as context for transparency

## `backend/app/engine/step_executor.py`

Purpose:
- dispatch to the correct execution logic by step type

Suggested method:

```python
async def execute_step(
    *,
    step: ExecutionStep,
    workflow_step: WorkflowStep,
    context: StepExecutionContext,
    session: Session
) -> StepResult:
    ...
```

Suggested `StepResult`:

```python
class StepResult(BaseModel):
    output_text: str
    tool_calls: list[ToolCallTrace] = []
```

Dispatch rules:
- `research` -> tool-enabled LLM loop
- `summarize` -> plain LLM call
- `draft` -> plain LLM call

## `backend/app/engine/runner.py`

Purpose:
- execute a workflow run from start to finish

Suggested methods:

```python
async def run_execution(execution_id: int) -> None: ...
async def resume_execution_from_step(execution_id: int, start_position: int) -> None: ...
```

Rules:
- mark execution `running` before beginning
- set `current_step_position` as each step starts
- mark step `running`, then `succeeded` or `failed`
- stop on first failure
- mark execution `succeeded` only when all steps complete
- mark execution `failed` when a step fails

## 6. LLM Integration Contracts

## `backend/app/llm/client.py`

Responsibilities:
- centralize OpenAI client setup
- keep model lookup/configuration out of business logic

Suggested helpers:

```python
def get_openai_client() -> OpenAI: ...
def get_default_model() -> str: ...
```

## `backend/app/llm/prompts.py`

Responsibilities:
- build system prompts for each step type
- standardize prompt structure

Suggested functions:

```python
def build_research_messages(...): ...
def build_summarize_messages(...): ...
def build_draft_messages(...): ...
```

## `backend/app/llm/tool_loop.py`

Responsibilities:
- run the research step with tool calling
- execute tool calls through the registry
- prevent runaway tool loops

Suggested API:

```python
async def run_research_with_tools(
    *,
    model: str,
    messages: list[dict[str, Any]],
    max_rounds: int = 3
) -> StepResult:
    ...
```

Loop rules:
- if the model returns final text, finish
- if the model emits a tool call, execute it
- append tool result and continue
- cap tool rounds
- serialize tool traces for persistence

## 7. Tool Contracts

## `backend/app/tools/registry.py`

Responsibilities:
- declare available tools
- map tool names to executors

Suggested contract:

```python
class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]
```

```python
def get_tool_definitions() -> list[ToolDefinition]: ...
async def execute_tool(name: str, arguments: dict[str, Any]) -> str: ...
```

## `backend/app/tools/http_fetch.py`

Responsibilities:
- fetch page content
- clean/truncate result

Suggested function:

```python
async def fetch_url(url: str) -> str: ...
```

Implementation notes:
- set timeout
- restrict payload size
- strip excessive markup where possible
- return readable text preview

## 8. API Routes And Response Expectations

## `backend/app/api/health.py`

Routes:
- `GET /api/health`

Response:

```json
{ "ok": true }
```

## `backend/app/api/workflows.py`

Routes:
- `GET /api/workflows`
- `POST /api/workflows`
- `GET /api/workflows/{workflow_id}`
- `PUT /api/workflows/{workflow_id}`
- `DELETE /api/workflows/{workflow_id}` optional

Implementation notes:
- return steps ordered by `position`
- validate non-empty workflow name
- validate step ordering

## `backend/app/api/executions.py`

Routes:
- `POST /api/workflows/{workflow_id}/executions`
- `GET /api/workflows/{workflow_id}/executions`
- `GET /api/executions/{execution_id}`
- `POST /api/executions/{execution_id}/steps/{execution_step_id}/retry`

Important behavior:
- execution creation should return quickly
- background task should continue execution after response returns

## 9. Frontend Type Draft

## `frontend/src/types/workflow.ts`

```ts
export type StepType = "research" | "summarize" | "draft";

export interface WorkflowStep {
  id: number;
  workflow_id: number;
  position: number;
  name: string;
  type: StepType;
  prompt_template: string;
  instructions?: string | null;
  model?: string | null;
  tool_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface Workflow {
  id: number;
  name: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
  steps: WorkflowStep[];
}

export interface WorkflowListItem {
  id: number;
  name: string;
  description?: string | null;
  step_count: number;
  updated_at: string;
}
```

## `frontend/src/types/execution.ts`

```ts
export type ExecutionStatus = "pending" | "running" | "succeeded" | "failed";

export interface ToolCallTrace {
  tool: string;
  arguments: Record<string, unknown>;
  result_preview: string;
}

export interface ExecutionStep {
  id: number;
  execution_id: number;
  workflow_step_id: number;
  position: number;
  name_snapshot: string;
  type_snapshot: "research" | "summarize" | "draft";
  status: ExecutionStatus;
  input_text?: string | null;
  output_text?: string | null;
  error_message?: string | null;
  tool_calls: ToolCallTrace[];
  attempt_count: number;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface Execution {
  id: number;
  workflow_id: number;
  status: ExecutionStatus;
  input_text: string;
  current_step_position?: number | null;
  error_message?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  created_at: string;
  steps: ExecutionStep[];
}
```

## 10. File-By-File Implementation Plan

The plan below is sequenced to produce a working vertical slice quickly.

## Phase 1: Backend Foundation

### File: `backend/requirements.txt`

Add:
- `fastapi`
- `uvicorn`
- `sqlmodel` or `sqlalchemy`
- `pydantic`
- `openai`
- `httpx`
- `python-dotenv`

Optional:
- `alembic`

### File: `backend/app/config.py`

Implement:
- environment loading
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `DATABASE_URL`

### File: `backend/app/db.py`

Implement:
- engine creation
- session dependency
- init_db helper

### File: `backend/app/main.py`

Implement:
- FastAPI app
- CORS for frontend dev server
- router registration
- startup DB init

### Files: `backend/app/models/workflow.py`, `backend/app/models/execution.py`

Implement:
- ORM models
- enums
- relationships

### Files: `backend/app/schemas/common.py`, `workflow.py`, `execution.py`

Implement:
- request/response Pydantic models

### File: `backend/app/api/health.py`

Implement:
- basic health route

## Phase 2: Workflow CRUD

### File: `backend/app/services/workflow_service.py`

Implement:
- create
- list
- get
- update

Decisions:
- on update, replace steps instead of patching in place
- normalize positions before save

### File: `backend/app/api/workflows.py`

Implement:
- workflow CRUD routes
- route-level validation and error mapping

### File: `backend/app/utils/errors.py`

Implement:
- `NotFoundError`
- `ValidationError`
- optional exception handlers

## Phase 3: Execution Persistence

### File: `backend/app/services/execution_service.py`

Implement:
- create execution
- snapshot execution steps from workflow steps
- get execution
- list workflow executions

Important:
- creation should not execute steps directly in the request code path

### File: `backend/app/api/executions.py`

Implement:
- create execution route
- get execution detail
- list workflow executions

### File: `backend/app/seed.py` optional

Implement:
- create a sample workflow for manual testing

## Phase 4: Execution Engine

### File: `backend/app/engine/context_builder.py`

Implement:
- derive current step input
- assemble previous output context

### File: `backend/app/engine/step_executor.py`

Implement:
- step type dispatch
- plain LLM execution helpers

### File: `backend/app/engine/runner.py`

Implement:
- sequential execution loop
- state transitions
- stop on failure
- overall execution status updates

Important:
- run this as a background task after execution creation

## Phase 5: LLM And Tool Calling

### File: `backend/app/llm/client.py`

Implement:
- OpenAI client bootstrap
- default model getter

### File: `backend/app/llm/prompts.py`

Implement:
- step-type-specific prompt assembly

### File: `backend/app/tools/http_fetch.py`

Implement:
- fetch URL
- truncate output
- return plain text

### File: `backend/app/tools/registry.py`

Implement:
- tool definitions
- tool execution dispatcher

### File: `backend/app/llm/tool_loop.py`

Implement:
- tool-calling loop for `research`
- tool trace capture
- max-round protection

### Update: `backend/app/engine/step_executor.py`

Add:
- `research` execution via tool loop

## Phase 6: Retry Semantics

### Update: `backend/app/services/execution_service.py`

Implement:
- retry validation
- reset target step and later steps
- increment `attempt_count`

### Update: `backend/app/api/executions.py`

Implement:
- retry route

### Update: `backend/app/engine/runner.py`

Implement:
- resume execution from a given step

## Phase 7: Frontend Foundation

### File: `frontend/package.json`

Create Vite React TypeScript app and add:
- `react-router-dom`
- `@tanstack/react-query`
- optional `clsx`

### File: `frontend/src/main.tsx`

Implement:
- React Query provider
- Router provider

### File: `frontend/src/App.tsx`

Implement:
- app routes

### Files: `frontend/src/types/workflow.ts`, `execution.ts`

Implement:
- frontend domain types

### File: `frontend/src/api/client.ts`

Implement:
- fetch wrapper
- base API URL handling

### Files: `frontend/src/api/workflows.ts`, `executions.ts`

Implement:
- typed API methods

## Phase 8: Workflow Builder UI

### File: `frontend/src/pages/WorkflowsPage.tsx`

Implement:
- workflow list
- create button

### File: `frontend/src/pages/WorkflowBuilderPage.tsx`

Implement:
- load workflow
- save workflow
- run workflow
- step selection/editing

### Files: `frontend/src/components/workflow/WorkflowForm.tsx`, `StepList.tsx`, `StepCard.tsx`, `StepEditor.tsx`, `AddStepMenu.tsx`

Implement:
- editable workflow name and description
- add/delete step
- move up/down
- edit step content

MVP note:
- use up/down buttons instead of drag-and-drop first

## Phase 9: Execution UI

### File: `frontend/src/pages/ExecutionPage.tsx`

Implement:
- fetch execution detail
- poll while running

### Files: `frontend/src/components/execution/ExecutionPanel.tsx`, `ExecutionStepCard.tsx`, `StatusBadge.tsx`, `RetryButton.tsx`

Implement:
- overall execution status
- per-step cards with:
  - status
  - input
  - output
  - error
  - tool traces
- retry action for failed steps

### File: `frontend/src/hooks/useExecutionPolling.ts`

Implement:
- poll every 1 second while execution is `running`

## Phase 10: Styling And DX Polish

### File: `frontend/src/styles/globals.css`

Implement:
- clean minimal layout
- readable cards and panels
- clear status colors

### File: `frontend/src/components/ui/*`

Implement:
- simple reusable form and button components

## Phase 11: Final Docs And Validation

### Update: `README.md`

After code exists, replace planning language with:
- exact setup commands
- exact file paths
- actual tool used
- exact screenshots or demo notes if desired

### Update: `DECISIONS.md`

After implementation, revise:
- what was actually built
- what changed from the plan

## 11. Codex TODO List

This is the direct execution order I would give Codex.

1. Scaffold `backend/` FastAPI app with config, DB, models, schemas, and routers.
2. Implement workflow CRUD end-to-end with SQLite persistence.
3. Implement execution creation and execution step snapshotting.
4. Implement execution detail API and workflow execution history API.
5. Implement sequential runner with step state transitions and error handling.
6. Implement plain LLM steps for `summarize` and `draft`.
7. Implement one tool and the `research` tool-calling loop.
8. Implement retry-from-failed-step semantics.
9. Scaffold `frontend/` Vite React app with routing and React Query.
10. Implement workflow list and workflow builder pages.
11. Implement execution detail page with polling.
12. Add failed-step retry action in the UI.
13. Add minimal styling and empty/loading/error states.
14. Update `README.md` and `DECISIONS.md` to reflect actual implementation.
15. Manually test the full flow with a sample workflow:
    - create workflow
    - run workflow
    - inspect outputs
    - trigger a failure
    - retry the failed step

## 12. Suggested Manual Test Cases

1. Create a workflow with three steps and save it.
2. Refresh the page and confirm the workflow persists.
3. Run the workflow and confirm status transitions:
   - pending -> running -> succeeded
4. Confirm step 2 receives step 1 output.
5. Confirm step 3 receives step 2 output.
6. Confirm research step can produce tool traces.
7. Force a tool or model failure and confirm:
   - step status becomes failed
   - execution status becomes failed
   - error is visible in the UI
8. Retry the failed step and confirm later steps rerun correctly.

## Final Implementation Principle

Keep the runtime semantics tighter than the UI ambition.

If time pressure appears, do not expand into graph editing, drag-and-drop, or streaming infrastructure. Preserve the parts that best communicate judgment:

- explicit state
- real chaining
- real tool calling
- visible failure
- retry semantics
