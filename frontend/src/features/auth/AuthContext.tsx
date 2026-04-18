import type { PropsWithChildren } from "react";
import { createContext, useEffect, useMemo, useState } from "react";

import { getCurrentUser, login as loginRequest, register as registerRequest } from "../../api/auth";
import type { LoginPayload, RegisterPayload, User } from "../../types/auth";

type AuthContextValue = {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isBootstrapping: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
};

const AUTH_STORAGE_KEY = "preterm.auth.token";

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  useEffect(() => {
    const storedToken = window.localStorage.getItem(AUTH_STORAGE_KEY);

    if (!storedToken) {
      setIsBootstrapping(false);
      return;
    }

    void (async () => {
      try {
        const currentUser = await getCurrentUser(storedToken);
        setToken(storedToken);
        setUser(currentUser);
      } catch {
        window.localStorage.removeItem(AUTH_STORAGE_KEY);
        setToken(null);
        setUser(null);
      } finally {
        setIsBootstrapping(false);
      }
    })();
  }, []);

  async function login(payload: LoginPayload) {
    const response = await loginRequest(payload);
    window.localStorage.setItem(AUTH_STORAGE_KEY, response.token.access_token);
    setToken(response.token.access_token);
    setUser(response.user);
  }

  async function register(payload: RegisterPayload) {
    const response = await registerRequest(payload);
    window.localStorage.setItem(AUTH_STORAGE_KEY, response.token.access_token);
    setToken(response.token.access_token);
    setUser(response.user);
  }

  function logout() {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    setToken(null);
    setUser(null);
  }

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token && user),
      isBootstrapping,
      login,
      register,
      logout,
    }),
    [isBootstrapping, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
