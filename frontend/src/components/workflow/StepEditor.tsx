import type { ChangeEvent } from "react";
import type { WorkflowPayloadStep } from "../../types/workflow";

interface StepEditorProps {
  step: WorkflowPayloadStep | undefined;
  onChange: (step: WorkflowPayloadStep) => void;
}

export function StepEditor({ step, onChange }: StepEditorProps) {
  if (!step) {
    return (
      <div className="panel">
        <div className="panel-title">Step Editor</div>
        <p className="muted">Select a step to edit.</p>
      </div>
    );
  }

  const update = (field: keyof WorkflowPayloadStep, value: string | boolean) => {
    onChange({ ...step, [field]: value });
  };

  return (
    <div className="panel">
      <div className="panel-title">Step Editor</div>
      <label>
        Name
        <input value={step.name} onChange={(event) => update("name", event.target.value)} />
      </label>
      <label>
        Type
        <select value={step.type} onChange={(event) => update("type", event.target.value as WorkflowPayloadStep["type"])}>
          <option value="research">research</option>
          <option value="summarize">summarize</option>
          <option value="draft">draft</option>
        </select>
      </label>
      <label>
        Prompt Template
        <textarea value={step.prompt_template} onChange={(event) => update("prompt_template", event.target.value)} rows={6} />
      </label>
      <label>
        Instructions
        <textarea value={step.instructions ?? ""} onChange={(event) => update("instructions", event.target.value)} rows={5} />
      </label>
      <label>
        Model
        <input value={step.model ?? ""} onChange={(event) => update("model", event.target.value)} placeholder="Optional" />
      </label>
      <label className="checkbox-row">
        <input
          checked={step.tool_enabled}
          onChange={(event: ChangeEvent<HTMLInputElement>) => update("tool_enabled", event.target.checked)}
          type="checkbox"
        />
        Enable tools
      </label>
    </div>
  );
}
