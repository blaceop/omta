import { useMutation } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { retryExecutionStep } from "../api/executions";
import { ExecutionStepCard } from "../components/execution/ExecutionStepCard";
import { StatusBadge } from "../components/execution/StatusBadge";
import { useExecutionPolling } from "../hooks/useExecutionPolling";

export function ExecutionPage() {
  const { executionId } = useParams();
  const executionQuery = useExecutionPolling(executionId);
  const retryMutation = useMutation({
    mutationFn: (executionStepId: number) => retryExecutionStep(executionId!, executionStepId),
    onSuccess: () => {
      executionQuery.refetch();
    }
  });

  if (executionQuery.isLoading) {
    return <p>Loading execution...</p>;
  }

  if (executionQuery.isError || !executionQuery.data) {
    return <p>Failed to load execution.</p>;
  }

  const execution = executionQuery.data;
  const completedSteps = execution.steps.filter((step) => step.status === "succeeded").length;
  const totalSteps = execution.steps.length;
  const activeStep =
    execution.steps.find((step) => step.status === "running") ??
    execution.steps.find((step) => step.position === execution.current_step_position) ??
    null;
  const retryErrorMessage = retryMutation.error instanceof Error ? retryMutation.error.message : null;

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <h1>Execution #{execution.id}</h1>
          <p className="muted">Inspect each step's state, output, and any tool traces.</p>
        </div>
        <StatusBadge status={execution.status} />
      </div>

      <div className="panel">
        <div className="panel-title">Execution Progress</div>
        <div className="execution-progress-summary">
          <strong>
            {completedSteps}/{totalSteps} steps completed
          </strong>
          <span className="muted">
            {activeStep ? `Currently running: Step ${activeStep.position + 1} — ${activeStep.name_snapshot}` : "No active step right now."}
          </span>
        </div>
        <div className="progress-track" aria-hidden="true">
          <div
            className="progress-fill"
            style={{ width: `${totalSteps === 0 ? 0 : (completedSteps / totalSteps) * 100}%` }}
          />
        </div>
      </div>

      <div className="panel">
        <div className="panel-title">Execution Input</div>
        <pre>{execution.input_text}</pre>
      </div>

      {retryErrorMessage ? (
        <div className="error-banner">
          Retry failed — {retryErrorMessage}
        </div>
      ) : null}

      <div className="execution-list">
        {execution.steps.map((step) => (
          <ExecutionStepCard
            key={step.id}
            step={step}
            onRetry={(executionStepId) => retryMutation.mutate(executionStepId)}
            retrying={retryMutation.isPending}
          />
        ))}
      </div>
    </div>
  );
}
