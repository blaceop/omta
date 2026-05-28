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

export interface WorkflowPayloadStep {
  id?: number;
  position: number;
  name: string;
  type: StepType;
  prompt_template: string;
  instructions?: string | null;
  model?: string | null;
  tool_enabled: boolean;
}

export interface WorkflowPayload {
  name: string;
  description?: string | null;
  steps: WorkflowPayloadStep[];
}
