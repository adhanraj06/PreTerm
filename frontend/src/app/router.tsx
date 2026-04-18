import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "../components/layout/ProtectedRoute";
import { AppShell } from "../components/layout/AppShell";
import { AuthGate } from "../features/auth/AuthGate";
import { LoginPage } from "../features/auth/LoginPage";
import { RegisterPage } from "../features/auth/RegisterPage";
import { HeadlinesPage } from "../features/headlines/HeadlinesPage";
import { MonitorPage } from "../features/monitor/MonitorPage";
import { PlannerPage } from "../features/planner/PlannerPage";
import { ResearchPage } from "../features/research/ResearchPage";
import { SettingsPage } from "../features/settings/SettingsPage";
import { WatchlistsPage } from "../features/watchlists/WatchlistsPage";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/app/monitor" replace />} />
        <Route path="/login" element={<AuthGate mode="public-only"><LoginPage /></AuthGate>} />
        <Route path="/register" element={<AuthGate mode="public-only"><RegisterPage /></AuthGate>} />
        <Route
          path="/app"
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/app/monitor" replace />} />
          <Route path="monitor/:marketId" element={<MonitorPage />} />
          <Route path="monitor" element={<MonitorPage />} />
          <Route path="watchlists" element={<WatchlistsPage />} />
          <Route path="headlines" element={<HeadlinesPage />} />
          <Route path="research" element={<ResearchPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="planner" element={<PlannerPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/app/monitor" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
