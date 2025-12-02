import { ServiceName } from "./types";

interface CredentialResponse {
  service_name: ServiceName;
  email: string | null;
}

async function handleResponse(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body?.detail || res.statusText || "Request failed";
    throw new Error(detail);
  }
  return (await res.json()) as CredentialResponse;
}

export async function loadCredentials(service: ServiceName): Promise<CredentialResponse> {
  const res = await fetch(`/api/credentials/${service}`);
  return handleResponse(res);
}

export async function saveCredentials(
  service: ServiceName,
  email: string,
  password: string,
): Promise<CredentialResponse> {
  const res = await fetch(`/api/credentials/${service}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return handleResponse(res);
}

export async function fetchEventMapping(): Promise<Record<string, string>> {
  const res = await fetch("/api/settings/event-mapping");
  if (!res.ok) {
    throw new Error("Failed to load event mapping");
  }
  const data = await res.json();
  return data.mapping || {};
}

export async function saveEventMapping(mapping: Record<string, string>): Promise<void> {
  const res = await fetch("/api/settings/event-mapping", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mapping }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail || "Failed to save mapping");
  }
}

export async function fetchFamlyEventTypes(): Promise<string[]> {
  const res = await fetch("/api/settings/famly-event-types");
  if (!res.ok) {
    throw new Error("Failed to load Famly event types");
  }
  const data = await res.json();
  return Array.isArray(data.types) ? data.types : [];
}
