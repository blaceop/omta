import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { createWorkflow, deleteWorkflow, fetchWorkflows } from "../api/workflows";
import type { WorkflowPayload } from "../types/workflow";

const defaultWorkflow: WorkflowPayload = {
  name: "New Workflow",
  description: "A simple multi-step workflow",
  steps: [
    {
      position: 0,
      name: "Research Topic",
      type: "research",
      prompt_template: "Research the topic and gather useful facts.",
      instructions: "Use tools if needed and return a structured result.",
      tool_enabled: true
    },
    {
      position: 1,
      name: "Summarize",
      type: "summarize",
      prompt_template: "Summarize the research findings into key points.",
      instructions: "Be concise. Use bullet points.",
      tool_enabled: false
    },
    {
      position: 2,
      name: "Draft Email",
      type: "draft",
      prompt_template: "Draft a professional internal email based on the summary.",
      instructions: "Keep it clear and actionable. End with next steps.",
      tool_enabled: false
    }
  ]
};

export function WorkflowsPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const workflowsQuery = useQuery({
    queryKey: ["workflows"],
    queryFn: fetchWorkflows,
    retry: 1
  });

  const createMutation = useMutation({
    mutationFn: () => createWorkflow(defaultWorkflow),
    onSuccess: async (workflow) => {
      await queryClient.invalidateQueries({ queryKey: ["workflows"] });
      navigate(`/workflows/${workflow.id}`);
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (workflowId: number) => deleteWorkflow(String(workflowId)),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["workflows"] });
    }
  });

  const handleDelete = (event: React.MouseEvent, workflowId: number, workflowName: string) => {
    event.preventDefault();
    event.stopPropagation();
    if (!window.confirm(`Delete "${workflowName}"? This will also remove all its executions.`)) return;
    deleteMutation.mutate(workflowId);
  };

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <h1>Workflows</h1>
          <p className="muted">Create a workflow, run it, and inspect every step.</p>
        </div>
        <button
          type="button"
          onClick={() => createMutation.mutate()}
          disabled={createMutation.isPending}
        >
          {createMutation.isPending ? "Creating..." : "New Workflow"}
        </button>
      </div>

      {createMutation.isError && (
        <div className="error-banner">
          Failed to create workflow — {(createMutation.error as Error).message}
        </div>
      )}

      {deleteMutation.isError && (
        <div className="error-banner">
          Failed to delete workflow — {(deleteMutation.error as Error).message}
        </div>
      )}

      <div className="panel">
        {workflowsQuery.isLoading && <p className="muted">Loading workflows...</p>}

        {workflowsQuery.isError && (
          <div>
            <p className="error-text">Failed to load workflows.</p>
            <p className="muted small">
              Make sure the backend is running: <code>uvicorn app.main:app --reload --port 8000</code>
            </p>
            <button type="button" onClick={() => workflowsQuery.refetch()} style={{ marginTop: "0.5rem" }}>
              Retry
            </button>
          </div>
        )}

        {workflowsQuery.data?.length === 0 && (
          <p className="muted">No workflows yet. Click "New Workflow" to get started.</p>
        )}

        <div className="workflow-list">
          {workflowsQuery.data?.map((workflow) => (
            <div key={workflow.id} className="workflow-card-row">
              <button
                type="button"
                className="workflow-card-link"
                onClick={() => navigate(`/workflows/${workflow.id}`)}
              >
                <div className="workflow-card-body">
                  <strong>{workflow.name}</strong>
                  <span className="muted">{workflow.description || "No description"}</span>
                  <span className="muted small">{workflow.step_count} step{workflow.step_count !== 1 ? "s" : ""}</span>
                </div>
              </button>
              <div className="workflow-card-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => navigate(`/workflows/${workflow.id}`)}
                >
                  Edit
                </button>
                <button
                  type="button"
                  className="btn-danger"
                  onClick={(event) => handleDelete(event, workflow.id, workflow.name)}
                  disabled={deleteMutation.isPending}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
