from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.executions import router as executions_router
from app.api.health import router as health_router
from app.api.workflows import router as workflows_router
from app.config import get_settings
from app.db import init_db
from app.models.execution import Execution, ExecutionStep
from app.models.workflow import Workflow, WorkflowStep


settings = get_settings()
app = FastAPI(title="Mini AI Workflow Builder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(workflows_router)
app.include_router(executions_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
