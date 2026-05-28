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

export interface ExecutionInputPayload {
  input_text: string;
}
