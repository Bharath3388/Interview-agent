import { AuthResponse, StartResponse, UserInfo, HistorySession, HistoryQA } from "@/types";

const BASE = "";

function authHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("authToken") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleResponse<T>(res: Response): Promise<T> {
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || "Request failed");
  }
  return data as T;
}

// ---- Auth ----
export async function apiRegister(username: string, email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });
  return handleResponse<AuthResponse>(res);
}

export async function apiLogin(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return handleResponse<AuthResponse>(res);
}

export async function apiGetMe(): Promise<UserInfo> {
  const res = await fetch(`${BASE}/api/auth/me`, {
    headers: authHeaders(),
  });
  return handleResponse<UserInfo>(res);
}

// ---- Interview ----
export async function apiStartInterview(formData: FormData): Promise<StartResponse> {
  const res = await fetch(`${BASE}/api/interview/start`, {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  });
  return handleResponse<StartResponse>(res);
}

// ---- History ----
export async function apiGetHistory(): Promise<HistorySession[]> {
  const res = await fetch(`${BASE}/api/auth/history`, {
    headers: authHeaders(),
  });
  return handleResponse<HistorySession[]>(res);
}

export async function apiGetSessionDetail(sessionId: string): Promise<{ session_id: string; qas: HistoryQA[] }> {
  const res = await fetch(`${BASE}/api/auth/history/${encodeURIComponent(sessionId)}`, {
    headers: authHeaders(),
  });
  return handleResponse<{ session_id: string; qas: HistoryQA[] }>(res);
}

// ---- WebSocket ----
// WebSocket must connect directly to the FastAPI backend (Next.js rewrites don't proxy WS)
const WS_HOST = process.env.NEXT_PUBLIC_WS_HOST || "localhost:8000";

export function createInterviewWS(sessionId: string): WebSocket {
  const protocol = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss:" : "ws:";
  return new WebSocket(`${protocol}//${WS_HOST}/ws/${sessionId}`);
}
