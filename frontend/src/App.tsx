import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { LandingPage } from "./pages/LandingPage";
import { DashboardPage } from "./pages/DashboardPage";
import { AuditorPage } from "./pages/AuditorPage";
import { LabPage } from "./pages/LabPage";
import { InventoryPage } from "./pages/InventoryPage";
import { AuditDetailPage } from "./pages/AuditDetailPage";
import { EcmPage } from "./pages/EcmPage";
import { ReportsPage } from "./pages/ReportsPage";
import { EvaluationPage } from "./pages/EvaluationPage";
import { ResearchPage } from "./pages/ResearchPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/app" element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="auditor" element={<AuditorPage />} />
          <Route path="inventory" element={<InventoryPage />} />
          <Route path="ecm" element={<EcmPage />} />
          <Route path="lab" element={<LabPage />} />
          <Route path="evaluation" element={<EvaluationPage />} />
          <Route path="research" element={<ResearchPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="audits/:auditId" element={<AuditDetailPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
