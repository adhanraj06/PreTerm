import type { PropsWithChildren } from "react";

import { AuthProvider } from "../features/auth/AuthContext";
import { HeadlineMapProvider } from "../features/headlines/HeadlineMapContext";
import { MonitorProvider } from "../features/monitor/MonitorContext";

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <AuthProvider>
      <MonitorProvider>
        <HeadlineMapProvider>{children}</HeadlineMapProvider>
      </MonitorProvider>
    </AuthProvider>
  );
}
