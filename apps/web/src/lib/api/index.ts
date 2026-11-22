import type { ApiClient } from "./client";
import { createMockClient } from "./mock/client";

let instance: ApiClient | undefined;

/**
 * Jedyne miejsce wyboru implementacji klienta.
 * NEXT_PUBLIC_API_MODE=mock (domyślnie). Tryb "http" pojawi się razem z backendem.
 */
export function getApi(): ApiClient {
  instance ??= createMockClient({ latencyMs: Number(process.env.NEXT_PUBLIC_MOCK_LATENCY_MS ?? 120), failKey: process.env.NEXT_PUBLIC_MOCK_FAIL_KEY === "1" });
  return instance;
}

export function setApiForTests(client: ApiClient | undefined) {
  instance = client;
}

export * from "./client";
export * from "./schemas";
