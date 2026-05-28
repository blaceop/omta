import { apiFetch } from "./client";
import type { Workflow, WorkflowListItem, WorkflowPayload } from "../types/workflow";

export function fetchWorkflows() {
  return apiFetch<WorkflowListItem[]>("/api/workflows");
}

export function fetchWorkflow(workflowId: string) {
  return apiFetch<Workflow>(`/api/workflows/${workflowId}`);
}

export function createWorkflow(payload: WorkflowPayload) {
  return apiFetch<Workflow>("/api/workflows", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateWorkflow(workflowId: string, payload: WorkflowPayload) {
  return apiFetch<Workflow>(`/api/workflows/${workflowId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function deleteWorkflow(workflowId: string) {
  return apiFetch<{ deleted: boolean; id: number }>(`/api/workflows/${workflowId}`, {
    method: "DELETE"
  });
}
