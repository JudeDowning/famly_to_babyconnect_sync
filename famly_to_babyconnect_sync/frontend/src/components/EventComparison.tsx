import React, { useMemo } from "react";
import { NormalisedEvent } from "../types";
import { assetUrl } from "../api";

type DateFormat = "weekday-mon-dd" | "weekday-dd-mon";

interface Props {
  famlyEvents: NormalisedEvent[];
  babyEvents: NormalisedEvent[];
  dateFormat: DateFormat;
  onSyncEvent?: (eventId: number) => void;
  syncingEventId?: number | null;
  isBulkSyncing?: boolean;
  showMissingOnly?: boolean;
  onToggleMissing?: () => void;
  controlsSlot?: React.ReactNode;
}

interface PairedRow {
  key: string;
  famly?: NormalisedEvent;
  baby?: NormalisedEvent;
  dayLabel: string;
  dayIso: string;
  timestamp: number;
}

const icon = (path: string) => assetUrl(path);

const defaultIconMap: Record<string, string> = {
  nappy: icon("/icons/diapers_v2.svg"),
  diaper: icon("/icons/diapers_v2.svg"),
  bottle: icon("/icons/bib_v2.svg"),
  solid: icon("/icons/eat_v2.svg"),
  meal: icon("/icons/eat_v2.svg"),
  meals: icon("/icons/eat_v2.svg"),
  sleep: icon("/icons/sleep_v2.svg"),
  medicine: icon("/icons/medicine_v2.svg"),
  temperature: icon("/icons/temperature_v2.svg"),
  bath: icon("/icons/bath_v2.svg"),
  message: icon("/icons/msg_v2.svg"),
};

const famlyIconMap: Record<string, string> = {
  nappy: icon("/icons/famly_diaper.svg"),
  "nappy change": icon("/icons/famly_diaper.svg"),
  diaper: icon("/icons/famly_diaper.svg"),
  solid: icon("/icons/famly_meals.svg"),
  meals: icon("/icons/famly_meals.svg"),
  meal: icon("/icons/famly_meals.svg"),
  sleep: icon("/icons/famly_sleep.svg"),
  "signed in": icon("/icons/famly_sign_in.svg"),
  "sign in": icon("/icons/famly_sign_in.svg"),
  "signed out": icon("/icons/famly_sign_out.svg"),
  "sign out": icon("/icons/famly_sign_out.svg"),
  ill: icon("/icons/famly_sick.svg"),
  sick: icon("/icons/famly_sick.svg"),
};

const SIGN_EVENT_TYPES = ["signed in", "sign in", "signed out", "sign out"];

const inferFamlyEventType = (event?: NormalisedEvent): string | undefined => {
  if (!event) return undefined;
  const base = (event.event_type || "").toLowerCase();
  if (SIGN_EVENT_TYPES.includes(base)) {
    return base;
  }
  const original = event.raw_data?.original_title?.toLowerCase() || "";
  if (original.includes("signed into") || original.includes("signed in")) {
    return "signed in";
  }
  if (original.includes("signed out")) {
    return "signed out";
  }
  return base || undefined;
};

const getIcon = (
  type: string | undefined | null,
  sourceLabel: string,
) => {
  if (!type) return null;
  const lower = type.toLowerCase();
  if (sourceLabel === "Baby Connect" && SIGN_EVENT_TYPES.includes(lower)) {
    return defaultIconMap["message"];
  }
  if (sourceLabel === "Famly") {
    return famlyIconMap[lower] || defaultIconMap[lower] || null;
  }
  return defaultIconMap[lower] || null;
};

const famlyDisplayMap: Record<string, string> = {
  solid: "Meals",
  meals: "Meals",
  meal: "Meals",
  nappy: "Nappy change",
  "nappy change": "Nappy change",
  sleep: "Sleep",
  "signed in": "Signed in",
  "sign in": "Signed in",
  "signed out": "Signed out",
  "sign out": "Signed out",
};

const babyDisplayMap: Record<string, string> = {
  nappy: "Diaper",
  diaper: "Diaper",
  solid: "Solid",
  meals: "Solid",
  meal: "Solid",
  sleep: "Sleep",
  bottle: "Bottle",
  medicine: "Medicine",
  temperature: "Temperature",
  bath: "Bath",
  message: "Message",
};

const getEventTitle = (type: string, sourceLabel: string) => {
  const lower = type.toLowerCase();
  if (sourceLabel === "Famly") {
    return famlyDisplayMap[lower] || type;
  }
  if (sourceLabel === "Baby Connect") {
    return babyDisplayMap[lower] || type;
  }
  return type;
};

const toDateKey = (iso: string) => new Date(iso).toISOString().slice(0, 10);

const getDayIso = (ev: NormalisedEvent) =>
  ev.raw_data?.day_date_iso || toDateKey(ev.start_time_utc);

const getSortTimestamp = (ev: NormalisedEvent) => {
  const start = new Date(ev.start_time_utc);
  let useEnd = false;
  if (ev.source_system === "baby_connect" && ev.event_type.toLowerCase().includes("sleep") && ev.end_time_utc) {
    const end = new Date(ev.end_time_utc);
    if (end.getTime() < start.getTime()) {
      useEnd = true;
    }
  }
  if (useEnd) {
    return new Date(ev.end_time_utc!).getTime();
  }
  return start.getTime();
};

const formatDayDisplay = (
  iso: string,
  fallback: string,
  format: DateFormat,
) => {
  if (!iso) return fallback;
  const date = new Date(`${iso}T00:00:00`);
  const weekday = date.toLocaleDateString(undefined, { weekday: "long" });
  const month = date.toLocaleDateString(undefined, { month: "short" });
  const day = date.toLocaleDateString(undefined, { day: "2-digit" });
  return format === "weekday-dd-mon"
    ? `${weekday} ${day} ${month}`
    : `${weekday} ${month} ${day}`;
};

const getEntrySplits = (event: NormalisedEvent) => {
  const detailLines = Array.isArray(event.raw_data?.detail_lines)
    ? event.raw_data!.detail_lines!
    : [];
  const splits: string[][] = [];
  let current: string[] = [];
  detailLines.forEach((line) => {
    if (/\d{1,2}:\d{2}/.test(line)) {
      if (current.length) splits.push(current);
      current = [line];
    } else {
      current.push(line);
    }
  });
  if (current.length) splits.push(current);
  if (!splits.length) {
    splits.push([]);
  }
  return splits;
};

const applyDegreeSymbol = (text: string) =>
  text.replace(/(\d+(?:\.\d+)?)\s*C\b/gi, "$1\u00B0C");

const buildPairs = (
  famlyEvents: NormalisedEvent[],
  babyEvents: NormalisedEvent[],
): PairedRow[] => {
  const map = new Map<string, PairedRow>();

  const makeKey = (ev: NormalisedEvent) => {
    const day = getDayIso(ev);
    const time = new Date(ev.start_time_utc).toISOString().slice(0, 16);
    const child = ev.child_name.toLowerCase();
    return `${day}-${ev.event_type}-${time}-${child}`;
  };

  const addEvent = (ev: NormalisedEvent, key: string, which: "famly" | "baby") => {
    if (!map.has(key)) {
    map.set(key, {
      key,
      dayLabel: ev.raw_data?.day_label || getDayIso(ev),
      dayIso: getDayIso(ev),
      timestamp: getSortTimestamp(ev),
    });
    }
    map.get(key)![which] = ev;
  };

  famlyEvents.forEach((ev) => {
    const splits = getEntrySplits(ev);
    splits.forEach((entry, idx) => {
      const clone: NormalisedEvent = {
        ...ev,
        summary: entry.join(" - ") || ev.summary || ev.raw_text || "",
        raw_data: {
          ...(ev.raw_data || {}),
          detail_lines: entry,
          source_event_id: ev.raw_data?.source_event_id ?? ev.id,
          split_index: idx,
        },
      };
      addEvent(clone, makeKey(clone), "famly");
    });
  });
  babyEvents.forEach((ev) => addEvent(ev, makeKey(ev), "baby"));

  return Array.from(map.values()).sort((a, b) => b.timestamp - a.timestamp);
};

const formatClock = (date: Date) =>
  date.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });

const to24Hour = (token: string) => {
  const trimmed = token.trim();
  const match = trimmed.match(/^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$/i);
  if (!match) return trimmed;
  let hour = parseInt(match[1], 10);
  const minute = match[2] ?? "00";
  const meridiem = match[3]?.toLowerCase();
  if (meridiem === "pm" && hour < 12) hour += 12;
  if (meridiem === "am" && hour === 12) hour = 0;
  return `${hour.toString().padStart(2, "0")}:${minute}`;
};

const formatRange24 = (range: string) => {
  const parts = range
    .split(/(?:-|to)/i)
    .map((part) => part.trim())
    .filter(Boolean);
  if (parts.length === 2) {
    return `${to24Hour(parts[0])} - ${to24Hour(parts[1])}`;
  }
  if (parts.length === 1) {
    return to24Hour(parts[0]);
  }
  return range.trim();
};

const stripTimePrefix = (
  text: string,
): { remaining: string | null; range: string | null } => {
  const trimmed = text.trim();
  const match = trimmed.match(
    /^(\d{1,2}:\d{2}(?:\s*[AaPp][Mm])?)(?:\s*(?:-|to)\s*(\d{1,2}:\d{2}(?:\s*[AaPp][Mm])?))?/i,
  );
  if (!match) {
    return { remaining: trimmed || null, range: null };
  }
  const [, startPart, endPart] = match;
  const range = endPart ? `${startPart} - ${endPart}` : startPart;
  const remainder = trimmed.slice(match[0].length).replace(/^[:\s-]+/, "");
  return { remaining: remainder || null, range };
};

const EventTile: React.FC<{ event?: NormalisedEvent; label: string }> = ({ event, label }) => {
  if (!event) {
    return <div className="event-card event-card--placeholder">No entry</div>;
  }
  const effectiveType =
    label === "Famly"
      ? inferFamlyEventType(event) || event.event_type
      : event.event_type;
  const icon = getIcon(effectiveType, label);
  const displayTitle = getEventTitle(effectiveType, label);
  const detailLines = Array.isArray(event.raw_data?.detail_lines)
    ? [...event.raw_data!.detail_lines!]
    : [];

  let displayTime = formatClock(
    new Date(
      event.source_system === "baby_connect" && event.end_time_utc
        ? event.end_time_utc
        : event.start_time_utc,
    ),
  );
  const cleanedEntries: string[] = [];
  detailLines.forEach((line) => {
    if (!line) return;
    const { remaining, range } = stripTimePrefix(line);
    if (range) {
      displayTime = formatRange24(range);
    }
    if (remaining) {
      cleanedEntries.push(remaining);
    }
  });

  const isSignEvent = SIGN_EVENT_TYPES.includes(
    (effectiveType || "").toLowerCase(),
  );

  const entries =
    cleanedEntries.length > 0
      ? cleanedEntries.map((line, idx) => ({
          key: `${event.id}-${idx}`,
          text: applyDegreeSymbol(line),
        }))
      : [
          {
            key: `${event.id}-summary`,
            text: applyDegreeSymbol(
              isSignEvent
                ? event.raw_data?.original_title ||
                    event.summary ||
                    event.raw_text ||
                    ""
                : event.summary || event.raw_text || "",
            ),
          },
        ];

  const noteText = event.raw_data?.note?.trim() || null;
  const normalizeValue = (value: string | null) =>
    value ? value.replace(/\s+/g, " ").trim().toLowerCase() : null;
  const noteMatchesEntry =
    noteText &&
    entries.some((entry) => normalizeValue(entry.text) === normalizeValue(applyDegreeSymbol(noteText)));
  const noteToShow = noteMatchesEntry ? null : noteText ? applyDegreeSymbol(noteText) : null;

  return (
    <div className="event-card">
      <div className="event-card__meta">
        <p className="event-card__title-line">
          <span className="event-card__title">{displayTitle}</span>
          <span className="event-card__time">{displayTime}</span>
        </p>
        {icon && <img src={icon} className="event-card__icon" alt="" />}
      </div>
      <ul className="event-card__list">
        {entries.map((entry) => (
          <li key={entry.key} className="event-card__summary">
            {entry.text}
          </li>
        ))}
      </ul>
      {noteToShow && <p className="event-card__note">{noteToShow}</p>}
    </div>
  );
};

export const EventComparison: React.FC<Props> = ({
  famlyEvents,
  babyEvents,
  dateFormat,
  onSyncEvent,
  syncingEventId = null,
  isBulkSyncing = false,
  showMissingOnly = false,
  onToggleMissing,
  controlsSlot,
}) => {
  const rows = useMemo(() => buildPairs(famlyEvents, babyEvents), [famlyEvents, babyEvents]);

  const stats = useMemo(() => {
    const famlyTotal = famlyEvents.length;
    const babyTotal = babyEvents.length;
    const missing = rows.filter((row) => row.famly && !row.baby).length;
    const matched = rows.filter((row) => row.famly && row.baby).length;
    return { famlyTotal, babyTotal, missing, matched };
  }, [famlyEvents, babyEvents, rows]);

  const filteredRows = showMissingOnly ? rows.filter((row) => row.famly && !row.baby) : rows;

  const grouped = filteredRows.reduce<Record<string, PairedRow[]>>((acc, row) => {
    acc[row.dayIso] = acc[row.dayIso] || [];
    acc[row.dayIso].push(row);
    return acc;
  }, {});

  const orderedGroups = Object.entries(grouped).sort(
    (a, b) => (b[1][0]?.timestamp || 0) - (a[1][0]?.timestamp || 0),
  );

  return (
    <>
      <div className="comparison-summary">
        <div>
          <p className="comparison-summary__label">Famly entries</p>
          <p className="comparison-summary__value">{stats.famlyTotal}</p>
        </div>
        <div>
          <p className="comparison-summary__label">Baby Connect entries</p>
          <p className="comparison-summary__value">{stats.babyTotal}</p>
        </div>
        <div>
          <p className="comparison-summary__label">Matched</p>
          <p className="comparison-summary__value">{stats.matched}</p>
        </div>
        <div>
          <p className="comparison-summary__label">Missing in Baby Connect</p>
          <p className="comparison-summary__value comparison-summary__value--alert">
            {stats.missing}
          </p>
        </div>
      </div>
      {controlsSlot && <div className="extra-controls">{controlsSlot}</div>}
      {showMissingOnly && filteredRows.length === 0 && (
        <p className="no-missing">No missing entries</p>
      )}
      {orderedGroups.map(([dayIso, entries]) => {
        const display = formatDayDisplay(
          dayIso,
          entries[0]?.dayLabel || dayIso,
          dateFormat,
        );
        return (
          <section key={dayIso} className="day-section">
            <div className="day-columns-header">
              <span className="day-columns-header__label">Famly</span>
              <span className="day-columns-header__day">{display}</span>
              <span className="day-columns-header__label day-columns-header__label--right">
                Baby Connect
              </span>
            </div>
            {entries.map((row) => {
              const isMatched = !!row.famly && !!row.baby;
              const famlyEventId =
                row.famly?.raw_data?.source_event_id ?? row.famly?.id;
              const showArrow = !!famlyEventId && !!row.famly && !row.baby && !!onSyncEvent;
              const isSyncingThis =
                !!famlyEventId && syncingEventId === famlyEventId;
              const arrowDisabled =
                !showArrow ||
                isBulkSyncing ||
                (syncingEventId !== null && !isSyncingThis);
              return (
                <div
                  key={row.key}
                  className={`pair-row${isMatched ? " pair-row--matched" : ""}`}
                >
                  <EventTile event={row.famly} label="Famly" />
                  <button
                    type="button"
                    className={`arrow-pill${isMatched ? " arrow-pill--matched" : ""}`}
                    disabled={arrowDisabled}
                    onClick={() => {
                      if (showArrow && famlyEventId) {
                        onSyncEvent?.(famlyEventId);
                      }
                    }}
                    aria-label={
                      isSyncingThis
                        ? "Syncing entry"
                        : showArrow
                        ? "Create this Famly entry in Baby Connect"
                        : isMatched
                        ? "Entry already synced"
                        : "No action"
                    }
                  >
                    {isSyncingThis
                      ? "…"
                      : showArrow
                      ? "→"
                      : isMatched
                      ? "✓"
                      : ""}
                  </button>
                  <EventTile event={row.baby} label="Baby Connect" />
                </div>
              );
            })}
          </section>
        );
      })}
    </>
  );
};
