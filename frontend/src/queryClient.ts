import { QueryClient } from "@tanstack/react-query";
import { ApiError } from "./api/errors";

export function createQueryClient({ retry = true }: { retry?: boolean } = {}): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Retry a network blip or a 5xx once. A 4xx will not change by asking again.
        retry: retry ? retryOnceUnlessClientError : false,
      },
    },
  });
}

function retryOnceUnlessClientError(failureCount: number, error: unknown): boolean {
  const clientError = error instanceof ApiError && error.status < 500;
  return !clientError && failureCount < 1;
}
