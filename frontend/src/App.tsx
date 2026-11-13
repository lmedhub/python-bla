import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router";
import { AuthProvider } from "./features/auth/AuthProvider";
import { createQueryClient } from "./queryClient";
import { AppRoutes } from "./routes/AppRoutes";

const queryClient = createQueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
