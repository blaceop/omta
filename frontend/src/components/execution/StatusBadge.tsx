import type { ExecutionStatus } from "../../types/execution";

export function StatusBadge({ status }: { status: ExecutionStatus }) {
  return <span className={`status-badge status-${status}`}>{status}</span>;
}
