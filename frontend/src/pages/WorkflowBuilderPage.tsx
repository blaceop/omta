import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createExecution } from "../api/executions";
import { deleteWorkflow, fetchWorkflow, updateWorkflow } from "../api/workflows";
import { StepEditor } from "../components/workflow/StepEditor";
import { StepList } from "../components/workflow/StepList";
import type { WorkflowPayload, WorkflowPayloadStep } from "../types/workflow";

function toPayload(data: NonNullable<Awaited<ReturnType<typeof fetchWorkflow>>>) : WorkflowPayload {
  return {
    name: data.name,
    description: data.description,
    steps: data.steps.map((step) => ({
      id: step.id,
      position: step.position,
      name: step.name,
      type: step.type,
      prompt_template: step.prompt_template,
      instructions: step.instructions,
      model: step.model,
      tool_enabled: step.tool_enabled
    }))
  };
}

export function WorkflowBuilderPage() {
  const { workflowId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [runInput, setRunInput] = useState("Research current AI workflow builder trends and draft an internal email summary.");

  const workflowQuery = useQuery({
    queryKey: ["workflow", workflowId],
    queryFn: () => fetchWorkflow(workflowId!),
    enabled: Boolean(workflowId)
  });

  const payload = useMemo(() => (workflowQuery.data ? toPayload(workflowQuery.data) : null), [workflowQuery.data]);
  const [draft, setDraft] = useState<WorkflowPayload | null>(null);
  const [hasLocalEdits, setHasLocalEdits] = useState(false);

  useEffect(() => {
    if (!payload) {
      return;
    }
    if (!hasLocalEdits || !draft) {
      setDraft(payload);
      setSelectedIndex((current) => Math.min(current, Math.max(0, payload.steps.length - 1)));
    }
  }, [payload, hasLocalEdits, draft]);

  const saveMutation = useMutation({
    mutationFn: (nextPayload: WorkflowPayload) => updateWorkflow(workflowId!, nextPayload),
    onSuccess: async (workflow) => {
      setDraft(toPayload(workflow));
      setHasLocalEdits(false);
      await queryClient.invalidateQueries({ queryKey: ["workflow", workflowId] });
      await queryClient.invalidateQueries({ queryKey: ["workflows"] });
    }
  });

  const runMutation = useMutation({
    mutationFn: () => createExecution(workflowId!, { input_text: runInput }),
    onSuccess: (execution) => navigate(`/executions/${execution.id}`)
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteWorkflow(workflowId!),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["workflows"] });
      navigate("/");
    }
  });

  const handleDelete = () => {
    const name = draft?.name ?? "this workflow";
    if (!window.confirm(`Delete "${name}"? This will also remove all its executions.`)) return;
    deleteMutation.mutate();
  };

  const updateStep = (index: number, nextStep: WorkflowPayloadStep) => {
    if (!draft) return;
    const steps = draft.steps.map((step, currentIndex) => (currentIndex === index ? nextStep : step));
    setHasLocalEdits(true);
    setDraft({ ...draft, steps });
  };

  const addStep = () => {
    if (!draft) return;
    const nextStep: WorkflowPayloadStep = {
      position: draft.steps.length,
      name: "New Step",
      type: "summarize",
      prompt_template: "Summarize the previous output.",
      instructions: "",
      tool_enabled: false
    };
    setHasLocalEdits(true);
    setDraft({ ...draft, steps: [...draft.steps, nextStep] });
    setSelectedIndex(draft.steps.length);
  };

  const moveStep = (index: number, direction: "up" | "down") => {
    if (!draft) return;
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= draft.steps.length) return;
    const nextSteps = [...draft.steps];
    [nextSteps[index], nextSteps[targetIndex]] = [nextSteps[targetIndex], nextSteps[index]];
    const normalized = nextSteps.map((step, position) => ({ ...step, position }));
    setHasLocalEdits(true);
    setDraft({ ...draft, steps: normalized });
    setSelectedIndex(targetIndex);
  };

  const removeStep = (index: number) => {
    if (!draft) return;
    const nextSteps = draft.steps.filter((_, currentIndex) => currentIndex !== index).map((step, position) => ({ ...step, position }));
    setHasLocalEdits(true);
    setDraft({ ...draft, steps: nextSteps });
    setSelectedIndex(Math.max(0, Math.min(selectedIndex, nextSteps.length - 1)));
  };

  if (workflowQuery.isLoading || !draft) {
    return <p className="muted">Loading workflow...</p>;
  }

  if (workflowQuery.isError) {
    return (
      <div className="page-stack">
        <p className="error-text">Failed to load workflow.</p>
        <button type="button" onClick={() => navigate("/")}>← Back to Workflows</button>
      </div>
    );
  }

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <button type="button" className="back-link" onClick={() => navigate("/")}>← Workflows</button>
          <h1>{draft.name}</h1>
          <p className="muted">Edit step prompts, ordering, and execution behavior.</p>
        </div>
        <div className="row">
          <button type="button" onClick={addStep}>Add Step</button>
          <button type="button" onClick={() => saveMutation.mutate(draft)} disabled={saveMutation.isPending}>
            {saveMutation.isPending ? "Saving..." : "Save"}
          </button>
          <button
            type="button"
            className="btn-danger"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? "Deleting..." : "Delete Workflow"}
          </button>
        </div>
      </div>

      {saveMutation.isError && (
        <div className="error-banner">
          Save failed — {(saveMutation.error as Error).message}
        </div>
      )}
      {runMutation.isError && (
        <div className="error-banner">
          Failed to start run — {(runMutation.error as Error).message}
        </div>
      )}
      {deleteMutation.isError && (
        <div className="error-banner">
          Delete failed — {(deleteMutation.error as Error).message}
        </div>
      )}

      <div className="builder-meta panel">
        <label>
          Workflow Name
          <input
            value={draft.name}
            onChange={(event) => {
              setHasLocalEdits(true);
              setDraft({ ...draft, name: event.target.value });
            }}
          />
        </label>
        <label>
          Description
          <textarea
            value={draft.description ?? ""}
            onChange={(event) => {
              setHasLocalEdits(true);
              setDraft({ ...draft, description: event.target.value });
            }}
            rows={3}
          />
        </label>
      </div>

      <div className="builder-grid">
        <StepList
          steps={draft.steps}
          selectedIndex={selectedIndex}
          onSelect={setSelectedIndex}
          onMove={moveStep}
          onRemove={removeStep}
        />
        <StepEditor step={draft.steps[selectedIndex]} onChange={(step) => updateStep(selectedIndex, step)} />
      </div>

      <div className="panel">
        <div className="panel-title">Run Workflow</div>
        <label>
          Initial Input
          <textarea value={runInput} onChange={(event) => setRunInput(event.target.value)} rows={4} />
        </label>
        <button type="button" onClick={() => runMutation.mutate()} disabled={runMutation.isPending || draft.steps.length === 0}>
          {runMutation.isPending ? "Starting..." : "Run Workflow"}
        </button>
        {draft.steps.length === 0 && <p className="muted small">Add at least one step before running.</p>}
      </div>
    </div>
  );
}
