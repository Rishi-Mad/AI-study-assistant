export class HttpError extends Error {
  status: number;
  body?: unknown;
  constructor(status: number, message: string, body?: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

const BASE_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

type FetchJSONOptions = {
  timeoutMs?: number;
  retries?: number;
  retryDelayMs?: number;
  headers?: Record<string, string>;
  signal?: AbortSignal;
};

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export async function fetchJSON<T>(
  path: string,
  init?: RequestInit,
  opts: FetchJSONOptions = {}
): Promise<T> {
  const {
    timeoutMs = 15_000,
    retries = 1,
    retryDelayMs = 600,
    headers = {},
    signal,
  } = opts;

  const url = `${BASE_URL}${path}`;
  let attempt = 0;

  while (true) {
    attempt += 1;

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    const mergedSignal = signal
      ? new AbortController()
      : controller;

    // Merge user signal if provided
    if (signal) {
      const ctrl = mergedSignal as AbortController;
      const onAbort = () => ctrl.abort();
      if (signal.aborted) onAbort();
      else signal.addEventListener("abort", onAbort, { once: true });
    }

    try {
      const res = await fetch(url, {
        ...init,
        headers: {
          "Content-Type": "application/json",
          ...headers,
          ...(init?.headers || {}),
        },
        signal: mergedSignal instanceof AbortController ? mergedSignal.signal : controller.signal,
      });

      if (!res.ok) {
        let body: unknown = undefined;
        try {
          body = await res.json();
        } catch {
          // ignore non-JSON error bodies
        }
        const msg = body && typeof body === "object" && "error" in (body as any)
          ? String((body as any).error)
          : `HTTP ${res.status} ${res.statusText}`;
        throw new HttpError(res.status, msg, body);
      }

      return res.json() as Promise<T>;
    } catch (err: any) {
      const isAbort = err?.name === "AbortError";
      const transient =
        isAbort || (err instanceof HttpError && [502, 503, 504].includes(err.status));

      if (attempt <= retries && transient) {
        clearTimeout(timeout);
        await sleep(retryDelayMs);
        continue;
      }

      if (isAbort) throw new Error("Request timed out. Check the server and try again.");
      throw err;
    } finally {
      clearTimeout(timeout);
    }
  }
}
