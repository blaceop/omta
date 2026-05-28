# Loom Walkthrough Script

This is a 3-5 minute walkthrough outline for the current implementation.

## Goal

Show that the app is a working mini AI workflow builder with:

- workflow authoring
- persisted execution state
- step-by-step visibility
- tool calling
- retry behavior
- honest tradeoffs

## Suggested Demo Setup

Before recording:

1. Start the backend:

```bash
cd /Users/guanby/Repos/omta/backend
.venv/bin/uvicorn app.main:app --reload --port 8000
```

2. Start the frontend:

```bash
cd /Users/guanby/Repos/omta/frontend
npm run dev -- --host 127.0.0.1
```

3. Make sure `backend/.env` is configured if you want to show a successful LLM path.

4. Keep one sample workflow ready:

- `Research Topic`
- `Summarize Findings`
- `Draft Email`

## 3-5 Minute Script

### 1. Intro and scope

Suggested narration:

> I built a mini AI workflow builder with a deliberately narrow scope. The goal was not a full agent platform, but a small working system that shows how I think about execution state, chaining, tool use, and tradeoffs.

### 2. Show the workflow list

Screen actions:

- open the workflows home page
- point to the workflow list

Suggested narration:

> The app starts with a list of saved workflows. These are persisted in SQLite, so they survive refreshes and restarts.

### 3. Open the workflow builder

Screen actions:

- open an existing workflow
- point to step list on the left
- point to the editor on the right

Suggested narration:

> The workflow model is intentionally linear. Each step has a type, a prompt template, instructions, and ordering. I support add, remove, and reorder so the builder is usable, but I intentionally stopped short of graph editing or branching.

### 4. Explain the step types

Screen actions:

- click through the three steps

Suggested narration:

> There are three step types right now: `research`, `summarize`, and `draft`. The important one is `research`, which is an agent-style step that can call tools. The later steps consume prior output, so the workflow is a real chain rather than isolated prompt calls.

### 5. Run the workflow

Screen actions:

- scroll to the run panel
- enter or keep a sample input
- click `Run Workflow`

Suggested narration:

> When I run the workflow, the backend creates an execution record and one execution-step record per workflow step. The frontend then polls the execution detail endpoint so the UI can show near-real-time progress.

### 6. Show the execution page

Screen actions:

- point to overall status
- point to each step card
- point to input, output, error, and tool trace sections

Suggested narration:

> This is the most important surface in the app. Instead of a black-box run button, each step exposes its own status, input, output, error, and any tool trace. That was a deliberate design choice because many agent builders break down when users can’t tell where or why a run failed.

### 7. Show failure and retry

If OpenAI connectivity is not working:

Suggested narration:

> In this environment the OpenAI request is failing, which actually gives a useful demonstration of the failure path. You can see the failure is persisted on the exact step that broke, and the later steps remain pending.

Screen actions:

- click `Retry Step`
- show that the step resets and reruns
- point out `attempt_count`

Suggested narration:

> Retry is implemented at the step level. When I retry, the failed step and downstream steps reset, the attempt count increments, and execution resumes from that point rather than forcing a full rerun from scratch.

If OpenAI connectivity is working:

Suggested narration:

> With a valid API key and connectivity, the same page shows successful research output, then the summarize step consumes it, then the draft step turns it into an email. The structure is the same either way, which is what I wanted from the execution model.

### 8. Explain tool calling

Suggested narration:

> The `research` step supports tool calling through the model loop. I implemented one tool, `http_fetch`, and the model can decide whether to use it. The tool is not exposed as a separate manual button, because the requirement was that the agent decides when to call it and incorporates the result into its reasoning.

### 9. Explain what you cut

Suggested narration:

> I intentionally did not build graph execution, queue infrastructure, streaming updates, or a broader tool platform. I wanted to spend the time on the runtime semantics instead: persistence, state transitions, retry behavior, and step transparency.

### 10. Close with production evolution

Suggested narration:

> If I were taking this toward production, the first architecture change I’d make would be moving execution out of the web process into a queue-plus-worker model, and then upgrading SQLite to Postgres. For this assignment, I kept it local and lightweight so the core system stayed easy to inspect and easy to run.

## Demo Order Summary

Use this order during recording:

1. Home page
2. Open workflow
3. Explain steps
4. Run workflow
5. Execution page
6. Failure or success path
7. Retry
8. Tool calling
9. Tradeoffs
10. Production next step
