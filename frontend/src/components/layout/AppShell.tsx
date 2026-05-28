import { Link } from "react-router-dom";
import type { PropsWithChildren } from "react";

export function AppShell({ children }: PropsWithChildren) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="brand">
          Mini AI Workflow Builder
        </Link>
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}
