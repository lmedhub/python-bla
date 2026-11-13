import { createContext, use, type ReactNode } from "react";
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

export function AuthProvider({ children }: { children: ReactNode }) {
  return children;
}

export function useAuth(): AuthContextValue {
  const value = use(AuthContext);
  if (value === null) {
    throw new Error("useAuth must be used inside <AuthProvider>.");
  }
  return value;
}
