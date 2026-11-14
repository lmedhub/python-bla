import { QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useLocation } from "react-router";
import { AuthProvider } from "../features/auth/AuthProvider";
import { createQueryClient } from "../queryClient";
import { AppRoutes } from "../routes/AppRoutes";

/** Shows the current URL, so tests can check that filters and page live in it. */
function CurrentUrl() {
  const location = useLocation();
  return <div data-testid="current-url">{location.pathname + location.search}</div>;
}

/** The whole app at `url`, as the browser would load it, against the MSW handlers. */
export function renderApp(url = "/tasks") {
  const user = userEvent.setup();
  const queryClient = createQueryClient({ retry: false });
  render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MemoryRouter initialEntries={[url]}>
          <AppRoutes />
          <CurrentUrl />
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>,
  );
  return { user, queryClient };
}
