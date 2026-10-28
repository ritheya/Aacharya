export const API = "http://127.0.0.1:8000";

// One helper for every backend call; turns error responses into readable messages.
export async function api(path, options = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(data?.detail ? JSON.stringify(data.detail) : `Request failed (${res.status})`);
  return data;
}
