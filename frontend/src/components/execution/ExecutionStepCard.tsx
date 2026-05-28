import type { ExecutionStep } from "../../types/execution";
import { StatusBadge } from "./StatusBadge";

interface ExecutionStepCardProps {
  step: ExecutionStep;
  onRetry?: (stepId: number) => void;
  retrying?: boolean;
}

export function ExecutionStepCard({ step, onRetry, retrying }: ExecutionStepCardProps) {
  return (
    <div className={`panel execution-step-card execution-step-${step.status}`}>
      <div className="step-card-header">
        <div>
          <strong>{step.position + 1}. {step.name_snapshot}</strong>
          <div className="muted small">
            {step.type_snapshot} · attempt {step.attempt_count}
          </div>
        </div>
        <StatusBadge status={step.status} />
      </div>
      <div className="step-card-section">
        <div className="label">Input</div>
        <pre>{step.input_text || "-"}</pre>
      </div>
      <div className="step-card-section">
        <div className="label">Output</div>
        <pre>{step.output_text || "-"}</pre>
      </div>
      <div className="step-card-section">
        <div className="label">Error</div>
        <pre>{step.error_message || "-"}</pre>
      </div>
      {step.error_message?.includes("Demo retry trigger") ? (
        <div className="demo-hint">
          This failure was intentionally triggered for a retry demo. Click <strong>Retry Step</strong> to rerun from here.
        </div>
      ) : null}
      <div className="step-card-section">
        <div className="label">Tool Calls</div>
        <pre>{JSON.stringify(step.tool_calls, null, 2) || "-"}</pre>
      </div>
      {step.status === "failed" && onRetry ? (
        <button type="button" onClick={() => onRetry(step.id)} disabled={retrying}>
          {retrying ? "Retrying..." : "Retry Step"}
        </button>
      ) : null}
    </div>
  );
}
