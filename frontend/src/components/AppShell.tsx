import { Outlet } from "react-router-dom";
import { Sidebar } from "./Layout";

export function AppShell() {
  return (
    <div className="flex min-h-screen bg-bg text-text">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 bg-surface/40">
        <Outlet />
      </div>
    </div>
  );
}
