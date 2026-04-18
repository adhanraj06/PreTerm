import type { PropsWithChildren } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "./useAuth";

type AuthGateProps = PropsWithChildren<{
  mode: "public-only" | "protected";
}>;

export function AuthGate({ mode, children }: AuthGateProps) {
  const { isAuthenticated, isBootstrapping } = useAuth();

  if (isBootstrapping) {
    return <div className="boot-screen">Loading PreTerm workspace...</div>;
  }

  if (mode === "public-only" && isAuthenticated) {
    return <Navigate to="/app/monitor" replace />;
  }

  if (mode === "protected" && !isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
