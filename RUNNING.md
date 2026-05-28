# Running The Project

This document is the fastest path to getting the app running locally for demo, testing, or Loom recording.

## Services

- Frontend: Vite + React app on `http://127.0.0.1:5173`
- Backend: FastAPI app on `http://127.0.0.1:8000`
- API health check: `http://127.0.0.1:8000/api/health`

## Prerequisites

- Node.js 20+ recommended
- Python 3.12+ recommended
- `backend/.env` populated with valid LLM settings

Current backend configuration expects these values:

```env
LLM_PROVIDER=bailian
LLM_API_KEY=your_key_here
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen3.5-plus
DATABASE_URL=sqlite:///./app.db
```

## 1. Start The Backend

Open a terminal and run:

```bash
cd /Users/guanby/Repos/omta/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Expected result:

- Uvicorn starts successfully
- Visiting `http://127.0.0.1:8000/api/health` returns:

```json
{"ok":true}
```

## 2. Start The Frontend

Open a second terminal and run:

```bash
cd /Users/guanby/Repos/omta/frontend
npm install
npm run dev -- --host 127.0.0.1
```

Expected result:

- Vite prints a local URL
- Open `http://127.0.0.1:5173`

## 3. Use The App

Suggested demo flow:

1. Open `http://127.0.0.1:5173`
2. Create or select a workflow
3. Add three steps such as `research -> summarize -> draft`
4. Save the workflow
5. Start a new execution with an input prompt like:

```text
Research recent AI workflow builder trends and draft an internal summary email.
```

6. Watch execution status update as each step runs
7. Open the execution detail view to inspect:
   - step input
   - step output
   - tool traces
   - any errors

## 4. Retry A Failed Step

If one step fails:

1. Open the execution detail page
2. Find the failed step
3. Trigger retry from the UI
4. The backend reruns that step and continues the remaining flow if successful

This is backed by persisted execution state in SQLite, so refreshes do not wipe progress history.

## 5. Stop The Services

- In each terminal, press `Ctrl+C`

If you started a server in the background, find it and stop it with:

```bash
lsof -i :8000
lsof -i :5173
kill <PID>
```

## 6. Common Issues

### Backend says API key is missing

Check `/Users/guanby/Repos/omta/backend/.env` and confirm `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL` are set.

### Frontend loads but API calls fail

Check that the backend is running on port `8000` and that `http://127.0.0.1:8000/api/health` responds.

### Research step looks weak or tool-heavy

That usually means the model made extra tool calls before producing its final answer. The app is designed to tolerate tool-level failures and keep the workflow moving when possible.

### Port already in use

Inspect the port owner:

```bash
lsof -i :8000
lsof -i :5173
```

Then stop the old process or start on a different port.

## 7. Current Verified Local Start

This repo was last verified locally with:

- Frontend running at `http://127.0.0.1:5173`
- Backend health check returning `{"ok":true}` from `http://127.0.0.1:8000/api/health`

## 8. Best Demo Setup

For a Loom recording or live walkthrough:

1. Start backend first
2. Start frontend second
3. Keep one browser tab on the workflow builder
4. Keep another browser tab on the execution detail page
5. Keep a terminal visible with backend logs in case you want to explain tool calling or retries
