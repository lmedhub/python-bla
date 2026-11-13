import { Navigate, Route, Routes } from "react-router";
import { AppLayout } from "../components/AppLayout";
import { LoginPage } from "../features/auth/LoginPage";
import { RequireAuth } from "../features/auth/RequireAuth";
import { TaskListPage } from "../features/tasks/TaskListPage";
import { NotFoundPage } from "./NotFoundPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route path="/tasks" element={<TaskListPage />} />
        </Route>
      </Route>
      <Route path="/" element={<Navigate to="/tasks" replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
