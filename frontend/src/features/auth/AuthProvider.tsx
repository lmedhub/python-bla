import { useQueryClient } from "@tanstack/react-query";
import { createContext, use, useEffect, useState, type ReactNode } from "react";
import { login, logout, onSessionEnded, refreshSession } from "../../api/session";
import type { User } from "../../api/types";

export type AuthState =
  | { status: "loading" }
  | { status: "signedOut" }
  | { status: "signedIn"; user: User };

interface AuthContextValue {
  state: AuthState;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const SIGNED_OUT: AuthState = { status: "signedOut" };

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [state, setState] = useState<AuthState>({ status: "loading" });

  useEffect(() => {
    let mounted = true;
    // The access token lives in memory, so a page load starts signed out. The refresh
    // cookie, if still valid, restores the session in one call.
    refreshSession().then(
      (session) => {
        if (mounted) setState(session ? { status: "signedIn", user: session.user } : SIGNED_OUT);
      },
      () => {
        if (mounted) setState(SIGNED_OUT);
      },
    );
    const unsubscribe = onSessionEnded(() => {
      queryClient.clear();
      setState(SIGNED_OUT);
    });
    return () => {
      mounted = false;
      unsubscribe();
    };
  }, [queryClient]);

  const value: AuthContextValue = {
    state,
    signIn: async (email, password) => {
      const session = await login(email, password);
      setState({ status: "signedIn", user: session.user });
    },
    signOut: async () => {
      await logout();
      // Nothing cached for one user may show up for the next one on this browser.
      queryClient.clear();
      setState(SIGNED_OUT);
    },
  };

  return <AuthContext value={value}>{children}</AuthContext>;
}

export function useAuth(): AuthContextValue {
  const value = use(AuthContext);
  if (value === null) {
    throw new Error("useAuth must be used inside <AuthProvider>.");
  }
  return value;
}

/** The signed-in user. Only for pages behind <RequireAuth>. */
export function useCurrentUser(): User {
  const { state } = useAuth();
  if (state.status !== "signedIn") {
    throw new Error("useCurrentUser must be used behind <RequireAuth>.");
  }
  return state.user;
}
