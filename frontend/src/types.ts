export type ServiceName = "famly" | "baby_connect";

export type ServiceStatus = "idle" | "ok" | "error";

export interface ConnectionStatus {
  service: ServiceName;
  email: string | null;
  status: ServiceStatus;
  message?: string;
}

export interface NormalisedEvent {
  id: number;
  source_system: ServiceName;
  child_name: string;
  event_type: string;
  start_time_utc: string;
  matched: boolean;
  summary?: string | null;
}
