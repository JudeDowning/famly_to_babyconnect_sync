export type ServiceName = "famly" | "baby_connect";

export type ServiceStatus = "idle" | "ok" | "error";

export interface ConnectionStatus {
  service: ServiceName;
  email: string | null;
  status: ServiceStatus;
  message?: string;
  lastConnectedAt?: string | null;
}

export interface NormalisedEvent {
  id: number;
  source_system: ServiceName;
  child_name: string;
  event_type: string;
  start_time_utc: string;
  matched: boolean;
  summary?: string | null;
  raw_text?: string | null;
  raw_data?: {
    day_label?: string;
    day_date_iso?: string | null;
    detail_lines?: string[];
    child_full_name?: string | null;
    event_datetime_iso?: string | null;
  } | null;
}
