import { setupServer } from "msw/node";

// No default handlers: each test declares the API responses it relies on.
export const server = setupServer();
