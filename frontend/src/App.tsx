import { Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { ExecutionPage } from "./pages/ExecutionPage";
import { WorkflowBuilderPage } from "./pages/WorkflowBuilderPage";
import { WorkflowsPage } from "./pages/WorkflowsPage";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<WorkflowsPage />} />
        <Route path="/workflows/:workflowId" element={<WorkflowBuilderPage />} />
        <Route path="/executions/:executionId" element={<ExecutionPage />} />
      </Routes>
    </AppShell>
  );
}
