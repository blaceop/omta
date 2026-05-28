import type { WorkflowPayloadStep } from "../../types/workflow";

interface StepListProps {
  steps: WorkflowPayloadStep[];
  selectedIndex: number;
  onSelect: (index: number) => void;
  onMove: (index: number, direction: "up" | "down") => void;
  onRemove: (index: number) => void;
}

export function StepList({ steps, selectedIndex, onSelect, onMove, onRemove }: StepListProps) {
  return (
    <div className="panel">
      <div className="panel-title">Steps</div>
      {steps.length === 0 ? <p className="muted">No steps yet.</p> : null}
      <div className="step-list">
        {steps.map((step, index) => (
          <button
            key={`${step.name}-${index}`}
            className={`step-list-item ${selectedIndex === index ? "selected" : ""}`}
            onClick={() => onSelect(index)}
            type="button"
          >
            <div>
              <strong>{index + 1}. {step.name || "Untitled step"}</strong>
              <div className="muted small">{step.type}</div>
            </div>
            <div className="step-actions">
              <button type="button" onClick={(event) => { event.stopPropagation(); onMove(index, "up"); }}>↑</button>
              <button type="button" onClick={(event) => { event.stopPropagation(); onMove(index, "down"); }}>↓</button>
              <button type="button" onClick={(event) => { event.stopPropagation(); onRemove(index); }}>Delete</button>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
