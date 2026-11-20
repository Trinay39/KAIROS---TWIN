const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export type ApiErrorKind = 'validation' | 'auth' | 'server' | 'network' | 'unknown';

export class ApiError extends Error {
  status?: number;
  kind: ApiErrorKind;
  userMessage: string;
  technicalMessage?: string;

  constructor({
    status,
    kind,
    userMessage,
    technicalMessage,
  }: {
    status?: number;
    kind: ApiErrorKind;
    userMessage: string;
    technicalMessage?: string;
  }) {
    super(userMessage);
    this.name = 'ApiError';
    this.status = status;
    this.kind = kind;
    this.userMessage = userMessage;
    this.technicalMessage = technicalMessage;
  }
}

function classifyStatus(status: number): ApiErrorKind {
  if (status === 400 || status === 422) return 'validation';
  if (status === 401 || status === 403) return 'auth';
  if (status >= 500) return 'server';
  return 'unknown';
}

function messageFor(path: string, kind: ApiErrorKind): string {
  if (kind === 'network') return 'Unable to connect to KAIROS-TWIN backend.';
  if (kind === 'auth') return 'KAIROS-TWIN backend access is not configured correctly.';
  if (path.startsWith('/predictions')) return 'Prediction service is unavailable.';
  if (path.startsWith('/states/compute')) return 'The selected student data could not be processed.';
  if (path.startsWith('/interventions') || path.startsWith('/outcomes')) return 'The intervention could not be recorded.';
  if (path.startsWith('/recommendations')) return 'Recommendation service is unavailable.';
  if (path.startsWith('/simulations')) return 'Simulation service is unavailable.';
  if (path.startsWith('/diagnostics')) return 'Diagnostics service is unavailable.';
  if (path.startsWith('/metadata')) return 'Model metadata is unavailable.';
  if (path.startsWith('/health')) return 'Unable to connect to KAIROS-TWIN backend.';
  return kind === 'server' ? 'KAIROS-TWIN backend reported a server error.' : 'The request could not be completed.';
}

async function readTechnicalDetail(res: Response): Promise<string> {
  try {
    const text = await res.text();
    if (!text) return `${res.status} ${res.statusText}`;
    try {
      const parsed = JSON.parse(text);
      return typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail ?? parsed);
    } catch {
      return text;
    }
  } catch {
    return `${res.status} ${res.statusText}`;
  }
}

export function statusForError(error: unknown) {
  if (error instanceof ApiError) {
    if (error.kind === 'validation') return 'validation_error';
    if (error.kind === 'auth') return 'auth_error';
    if (error.kind === 'server') return 'server_error';
    if (error.kind === 'network') return 'network_error';
  }
  return 'error';
}

export function messageForError(error: unknown, fallback: string): string {
  if (error instanceof ApiError) return error.userMessage;
  return error instanceof Error ? error.message : fallback;
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const key = import.meta.env.VITE_KAIROS_TWIN_API_KEY || '';
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(key ? { Authorization: `Bearer ${key}` } : {}),
        ...(init?.headers || {}),
      },
    });
  } catch (error) {
    const apiError = new ApiError({
      kind: 'network',
      userMessage: messageFor(path, 'network'),
      technicalMessage: error instanceof Error ? error.message : String(error),
    });
    if (import.meta.env.DEV) console.error(apiError.technicalMessage);
    throw apiError;
  }

  if (!res.ok) {
    const kind = classifyStatus(res.status);
    const technicalMessage = await readTechnicalDetail(res);
    if (import.meta.env.DEV) console.error(`API ${res.status} ${path}: ${technicalMessage}`);
    throw new ApiError({
      status: res.status,
      kind,
      userMessage: messageFor(path, kind),
      technicalMessage,
    });
  }
  try {
    return await res.json() as T;
  } catch (error) {
    const apiError = new ApiError({
      status: res.status,
      kind: 'unknown',
      userMessage: messageFor(path, 'unknown'),
      technicalMessage: error instanceof Error ? error.message : String(error),
    });
    if (import.meta.env.DEV) console.error(`API invalid JSON ${path}: ${apiError.technicalMessage}`);
    throw apiError;
  }
}
