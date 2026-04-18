import { useEffect, useMemo, useState } from "react";
import { NavLink, Outlet, useLocation, matchPath } from "react-router-dom";

import { getNotifications, markNotificationRead, type Notification } from "../../api/alerts";
import { useAuth } from "../../features/auth/useAuth";
import { CopilotPanel } from "../../features/copilot/CopilotPanel";

const navItems = [
  { to: "/app/monitor", label: "Monitor", hint: "Core workstation" },
  { to: "/app/watchlists", label: "Watchlists", hint: "Saved focus sets" },
  { to: "/app/headlines", label: "Headlines", hint: "News mapping desk" },
  { to: "/app/research", label: "Research", hint: "Stocks, SEC, macro" },
  { to: "/app/planner", label: "Planner", hint: "Hedge planning" },
  { to: "/app/settings", label: "Settings", hint: "Profile and preferences" },
];

const routeMeta: Record<string, { eyebrow: string; title: string; subtitle: string }> = {
  "/app/monitor": {
    eyebrow: "Primary Desk",
    title: "Market Monitor",
    subtitle: "Track active contracts, inspect event briefs, and keep the main desk focused.",
  },
  "/app/watchlists": {
    eyebrow: "Personalization",
    title: "Watchlists",
    subtitle: "Save the contracts and themes that deserve repeated attention.",
  },
  "/app/headlines": {
    eyebrow: "Event Mapping",
    title: "Headlines Desk",
    subtitle: "Map events, inspect sentiment, and connect incoming news to the right market.",
  },
  "/app/research": {
    eyebrow: "Data",
    title: "Research",
    subtitle: "Equity prices, SEC filings, and FRED macro series without tying to a Kalshi contract.",
  },
  "/app/planner": {
    eyebrow: "Risk Planning",
    title: "Planner",
    subtitle: "Use markets as lightweight planning support for important real-world dates.",
  },
  "/app/settings": {
    eyebrow: "Account",
    title: "Settings",
    subtitle: "Manage profile, desk defaults, alerts, and workspace preferences.",
  },
  "/app/monitor/detail": {
    eyebrow: "Contract",
    title: "Market detail",
    subtitle: "Price history and Kalshi resolution context.",
  },
};

export function AppShell() {
  const location = useLocation();
  const { user, token, logout } = useAuth();
  const meta = useMemo(() => {
    if (matchPath("/app/monitor/:marketId", location.pathname)) {
      return routeMeta["/app/monitor/detail"];
    }
    return routeMeta[location.pathname] ?? routeMeta["/app/monitor"];
  }, [location.pathname]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [trayOpen, setTrayOpen] = useState(false);

  useEffect(() => {
    if (!token) {
      return;
    }
    const authToken = token;

    let active = true;
    async function load() {
      try {
        const data = await getNotifications(authToken);
        if (!active) {
          return;
        }
        setNotifications(data);
      } catch {
        if (!active) {
          return;
        }
        setNotifications([]);
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, [token, location.pathname]);

  const unreadCount = useMemo(
    () => notifications.filter((notification) => !notification.is_read).length,
    [notifications],
  );

  async function handleMarkRead(notificationId: number) {
    if (!token) {
      return;
    }
    try {
      const updated = await markNotificationRead(token, notificationId);
      setNotifications((current) =>
        current.map((notification) => (notification.id === updated.id ? updated : notification)),
      );
    } catch {
      // Keep tray resilient on single-item failure.
    }
  }

  return (
    <div className="workstation-shell">
      <aside className="workspace-rail">
        <div className="brand-cluster">
          <div className="brand-mark">PT</div>
          <div>
            <span className="eyebrow">Prediction Market Workstation</span>
            <h1>PreTerm</h1>
          </div>
        </div>

        <section className="identity-card">
          <span className="section-kicker">Signed In</span>
          <strong>{user?.display_name}</strong>
          <span className="identity-meta">{user?.email}</span>
          <span className="identity-meta">
            Focus: {user?.profile.default_market_focus ?? "General desk"}
          </span>
        </section>

        <nav className="workspace-nav" aria-label="Workspace navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/app/monitor"}
              className={({ isActive }) =>
                isActive ? "workspace-nav-item active" : "workspace-nav-item"
              }
            >
              <span>{item.label}</span>
              <small>{item.hint}</small>
            </NavLink>
          ))}
        </nav>

        <section className="rail-footer-card rail-footer-minimal">
          <span className="section-kicker">Feed</span>
          <p>Markets refresh on a timer when Kalshi is enabled. Pins stay in this browser session.</p>
        </section>
      </aside>

      <div className="workstation-main">
        <header className="top-header">
          <div>
            <span className="eyebrow">{meta.eyebrow}</span>
            <h2>{meta.title}</h2>
            <p>{meta.subtitle}</p>
          </div>

          <div className="header-actions">
            <button
              type="button"
              className={trayOpen ? "ghost-button active" : "ghost-button"}
              onClick={() => setTrayOpen((current) => !current)}
            >
              Alerts {unreadCount > 0 ? `(${unreadCount})` : ""}
            </button>
            <div className="user-chip">
              <span className="user-chip-label">Desk User</span>
              <strong>{user?.display_name}</strong>
            </div>
            <button type="button" className="ghost-button" onClick={logout}>
              Log Out
            </button>
          </div>
        </header>

        {trayOpen ? (
          <section className="notification-tray">
            <div className="panel-heading">
              <div>
                <span className="section-kicker">Notifications</span>
                <h4>Triggered alerts</h4>
              </div>
              <small>{unreadCount} unread</small>
            </div>

            {notifications.length === 0 ? (
              <div className="empty-state">
                No triggered alerts yet. Add markets to watchlists and enable alert rules.
              </div>
            ) : (
              <div className="stacked-cards compact-stack">
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={notification.is_read ? "notification-card read" : "notification-card"}
                  >
                    <div className="list-card-header">
                      <div>
                        <strong>{notification.title}</strong>
                        <small>{new Date(notification.created_at).toLocaleString()}</small>
                      </div>
                      {!notification.is_read ? (
                        <button
                          type="button"
                          className="mini-button"
                          onClick={() => void handleMarkRead(notification.id)}
                        >
                          Mark Read
                        </button>
                      ) : null}
                    </div>
                    <p>{notification.message}</p>
                  </div>
                ))}
              </div>
            )}
          </section>
        ) : null}

        <div className="workspace-grid">
          <main className="main-surface">
            <Outlet />
          </main>

          <aside className="insight-panel">
            <CopilotPanel />

            <div className="insight-card">
              <span className="section-kicker">User Context</span>
              <ul className="meta-list">
                <li>Theme: {user?.profile.theme ?? "system"}</li>
                <li>Timezone: {user?.profile.timezone ?? "Not set"}</li>
                <li>
                  Headlines alerts: {user?.preference.alert_headline_matches ? "Enabled" : "Off"}
                </li>
              </ul>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
