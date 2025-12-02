import React, { useMemo } from "react";
import { NormalisedEvent } from "../types";

type DateFormat = "weekday-mon-dd" | "weekday-dd-mon";

interface Props {
  famlyEvents: NormalisedEvent[];
  babyEvents: NormalisedEvent[];
  dateFormat: DateFormat;
}

interface PairedRow {
  key: string;
  famly?: NormalisedEvent;
  baby?: NormalisedEvent;
  dayLabel: string;
  dayIso: string;
  timestamp: number;
}

const defaultIconMap: Record<string, string> = {
  nappy: "/icons/diapers_v2.svg",
  diaper: "/icons/diapers_v2.svg",
  bottle: "/icons/bib_v2.svg",
  solid: "/icons/eat_v2.svg",
  meal: "/icons/eat_v2.svg",
  meals: "/icons/eat_v2.svg",
  sleep: "/icons/sleep_v2.svg",
  medicine: "/icons/medicine_v2.svg",
  temperature: "/icons/temperature_v2.svg",
  bath: "/icons/bath_v2.svg",
  message: "/icons/msg_v2.svg",
};

const famlyIconMap: Record<string, string> = {
  nappy: "/icons/famly_diaper.svg",
  "nappy change": "/icons/famly_diaper.svg",
  diaper: "/icons/famly_diaper.svg",
  solid: "/icons/famly_meals.svg",
  meals: "/icons/famly_meals.svg",
  meal: "/icons/famly_meals.svg",
  sleep: "/icons/famly_sleep.svg",
  "signed in": "/icons/famly_sign_in.svg",
  "sign in": "/icons/famly_sign_in.svg",
  "signed out": "/icons/famly_sign_out.svg",
  "sign out": "/icons/famly_sign_out.svg",
  ill: "/icons/famly_sick.svg",
  sick: "/icons/famly_sick.svg",
};

const SIGN_EVENT_TYPES = ["signed in", "sign in", "signed out", "sign out"];

const getIcon = (type: string | undefined | null, sourceLabel: string) => {
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

const getDayIso = (ev: NormalisedEvent) =>
  ev.raw_data?.day_date_iso || new Date(ev.start_time_utc).toISOString().slice(0, 10);

const getTimestamp = (ev: NormalisedEvent) => {
  const raw = ev.raw_data?.event_datetime_iso || ev.start_time_utc;
  return new Date(raw).getTime();
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
        timestamp: getTimestamp(ev),
      });
    }
    map.get(key)![which] = ev;
  };

  famlyEvents.forEach((ev) => {
    const splits = getEntrySplits(ev);
    splits.forEach((entry, idx) => {
      const clone: NormalisedEvent = {
        ...ev,
        id: ev.id * 100 + idx,
        summary: entry.join(" - ") || ev.summary || ev.raw_text || "",
        raw_data: {
          ...ev.raw_data,
          detail_lines: entry,
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
  });

const stripTimePrefix = (text: string): { remaining: string | null; range: string | null } => {
  const trimmed = text.trim();
  const match = trimmed.match(/^(\d{1,2}:\d{2})(\s*-\s*(\d{1,2}:\d{2}))?/);
  if (!match) {
    return { remaining: trimmed || null, range: null };
  }
  const range = match[0];
  const remainder = trimmed.slice(range.length).replace(/^[:\s-]+/, "");
  return { remaining: remainder || null, range };
};

const EventTile: React.FC<{ event?: NormalisedEvent; label: string }> = ({ event, label }) => {
  if (!event) {
    return <div className="event-card event-card--placeholder">No entry</div>;
  }
  const icon = getIcon(event.event_type, label);
  const displayTitle = getEventTitle(event.event_type, label);
  const detailLines = Array.isArray(event.raw_data?.detail_lines)
    ? [...event.raw_data!.detail_lines!]
    : [];

  let displayTime = formatClock(new Date(event.start_time_utc));
  const cleanedEntries: string[] = [];
  detailLines.forEach((line) => {
    if (!line) return;
    const { remaining, range } = stripTimePrefix(line);
    if (range && range.includes("-")) {
      displayTime = range;
    }
    if (remaining) {
      cleanedEntries.push(remaining);
    }
  });

const isSignEvent = SIGN_EVENT_TYPES.includes((event.event_type || "").toLowerCase());

  const entries =
    cleanedEntries.length > 0
      ? cleanedEntries.map((line, idx) => ({
          key: `${event.id}-${idx}`,
          text: line,
        }))
      : isSignEvent
      ? []
      : [
          {
            key: `${event.id}-summary`,
            text: event.summary || event.raw_text || "",
          },
        ];

  return (
    <div className="event-card">
      <div className="event-card__meta">
        <div>
          <p className="event-card__label">{label}</p>
          <p className="event-card__title-line">
            <span className="event-card__title">{displayTitle}</span>
            <span className="event-card__time">{displayTime}</span>
          </p>
        </div>
        {icon && <img src={icon} className="event-card__icon" alt="" />}
      </div>
      <ul className="event-card__list">
        {entries.map((entry) => (
          <li key={entry.key} className="event-card__summary">
            {entry.text}
          </li>
        ))}
      </ul>
      {event.raw_data?.note && <p className="event-card__note">{event.raw_data.note}</p>}
    </div>
  );
};

export const EventComparison: React.FC<Props> = ({ famlyEvents, babyEvents, dateFormat }) => {
  const rows = useMemo(() => buildPairs(famlyEvents, babyEvents), [famlyEvents, babyEvents]);

  const stats = useMemo(() => {
    const famlyTotal = famlyEvents.length;
    const babyTotal = babyEvents.length;
    const missing = rows.filter((row) => row.famly && !row.baby).length;
    const matched = rows.filter((row) => row.famly && row.baby).length;
    return { famlyTotal, babyTotal, missing, matched };
  }, [famlyEvents, babyEvents, rows]);

  const grouped = rows.reduce<Record<string, PairedRow[]>>((acc, row) => {
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
      {orderedGroups.map(([dayIso, entries]) => {
        const display = formatDayDisplay(
          dayIso,
          entries[0]?.dayLabel || dayIso,
          dateFormat,
        );
        return (
          <section key={dayIso} className="day-section">
            <h4 className="day-title">{display}</h4>
            {entries.map((row) => {
              const isMatched = !!row.famly && !!row.baby;
              const showArrow = !!row.famly && !row.baby;
              return (
                <div
                  key={row.key}
                  className={`pair-row${isMatched ? " pair-row--matched" : ""}`}
                >
                  <EventTile event={row.famly} label="Famly" />
                  <button
                    type="button"
                    className={`arrow-pill${isMatched ? " arrow-pill--matched" : ""}`}
                    disabled={!showArrow}
                    onClick={() => {
                      if (showArrow) {
                        console.log("Trigger BabyConnect push for", row.famly?.id);
                      }
                    }}
                    aria-label={
                      showArrow
                        ? "Create this Famly entry in Baby Connect"
                        : isMatched
                        ? "Entry already synced"
                        : "No action"
                    }
                  >
                    {showArrow ? "→" : isMatched ? "✓" : ""}
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
