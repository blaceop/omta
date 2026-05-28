import { apiFetch } from "./client";
import type { Execution, ExecutionInputPayload } from "../types/execution";

export function createExecution(workflowId: string, payload: ExecutionInputPayload) {
  return apiFetch<Execution>(`/api/workflows/${workflowId}/executions`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function fetchExecution(executionId: string) {
  return apiFetch<Execution>(`/api/executions/${executionId}`);
}

export function retryExecutionStep(executionId: string, executionStepId: number) {
  return apiFetch<Execution>(`/api/executions/${executionId}/steps/${executionStepId}/retry`, {
    method: "POST"
  });
}
