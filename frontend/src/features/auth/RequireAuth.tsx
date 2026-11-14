import { Navigate, Outlet, useLocation } from "react-router";
import { useAuth } from "./AuthProvider";

export function RequireAuth() {
  const { state } = useAuth();
  const location = useLocation();

  if (state.status === "loading") {
    return <p role="status">Loading…</p>;
  }
  if (state.status === "signedOut") {
    // Remember where the visitor was going, so signing in takes them there.
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  }
  return <Outlet />;
}
