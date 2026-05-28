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
