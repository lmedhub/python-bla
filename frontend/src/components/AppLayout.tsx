import { Link, Outlet } from "react-router";
import { useAuth, useCurrentUser } from "../features/auth/AuthProvider";
import styles from "./AppLayout.module.css";

export function AppLayout() {
  const user = useCurrentUser();
  const { signOut } = useAuth();

  return (
    <>
      <header className={styles.header}>
        <Link to="/tasks" className={styles.brand}>
          Task Manager
        </Link>
        <span className={styles.user}>{user.name}</span>
        <button type="button" className="secondary" onClick={() => void signOut()}>
          Sign out
        </button>
      </header>
      <main className={styles.main}>
        <Outlet />
      </main>
    </>
  );
}
