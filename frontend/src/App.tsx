import React, { useEffect, useMemo, useState } from "react";
import { ConnectionStatus, NormalisedEvent, ServiceName } from "./types";
import { SettingsDrawer } from "./components/SettingsDrawer";
import { EventComparison } from "./components/EventComparison";

type DateFormat = "weekday-mon-dd" | "weekday-dd-mon";

const buildEventKey = (event: NormalisedEvent) => {
  const dayIso =
    event.raw_data?.day_date_iso ||
    new Date(event.start_time_utc).toISOString().slice(0, 10);
  const time = new Date(event.start_time_utc).toISOString().slice(0, 16);
  const child = (event.child_name || "").toLowerCase();
  return `${dayIso}-${event.event_type}-${time}-${child}`;
};

const computeMissingCount = (
  famlyEvents: NormalisedEvent[],
  babyEvents: NormalisedEvent[],
) => {
  const babyKeys = new Set(babyEvents.map((event) => buildEventKey(event)));
  return famlyEvents.reduce((count, event) => {
    const key = buildEventKey(event);
    return babyKeys.has(key) ? count : count + 1;
  }, 0);
};

const App: React.FC = () => {
  const [famlyStatus, setFamlyStatus] = useState<ConnectionStatus>({
    service: "famly",
    email: null,
    status: "idle",
    lastConnectedAt: null,
  });
  const [bcStatus, setBcStatus] = useState<ConnectionStatus>({
    service: "baby_connect",
    email: null,
    status: "idle",
    lastConnectedAt: null,
  });
  const [famlyEvents, setFamlyEvents] = useState<NormalisedEvent[]>([]);
  const [bcEvents, setBcEvents] = useState<NormalisedEvent[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [scrapeDaysBack, setScrapeDaysBack] = useState(0);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [dateFormat, setDateFormat] = useState<DateFormat>("weekday-mon-dd");

  const fetchStatus = async () => {
    const res = await fetch("/api/status");
    const data = await res.json();

    setFamlyStatus({
      service: "famly",
      email: data.famly.email,
      status: data.famly.has_credentials ? "ok" : "idle",
      message: undefined,
      lastConnectedAt: data.famly.last_connected_at,
    });

    setBcStatus({
      service: "baby_connect",
      email: data.baby_connect.email,
      status: data.baby_connect.has_credentials ? "ok" : "idle",
      message: undefined,
      lastConnectedAt: data.baby_connect.last_connected_at,
    });
  };

  const fetchEvents = async () => {
    const [famlyRes, bcRes] = await Promise.all([
      fetch("/api/events?source=famly"),
      fetch("/api/events?source=baby_connect"),
    ]);
    setFamlyEvents(await famlyRes.json());
    setBcEvents(await bcRes.json());
  };

  useEffect(() => {
    fetchStatus();
    fetchEvents();
  }, []);

  const handleTestConnection = async (service: ServiceName) => {
    // For now, just ping /api/status to simulate an update.
    await fetchStatus();
  };

  const scrapeFamly = async (daysBack: number) => {
    const res = await fetch(`/api/scrape/famly?days_back=${daysBack}`, { method: "POST" });
    if (!res.ok) {
      throw new Error("Failed to scrape Famly");
    }
  };

  const scrapeBabyConnect = async (daysBack: number) => {
    const res = await fetch(`/api/scrape/baby_connect?days_back=${daysBack}`, {
      method: "POST",
    });
    if (!res.ok) {
      throw new Error("Failed to scrape Baby Connect");
    }
  };

  const markConnectionError = (service: ServiceName) => {
    if (service === "famly") {
      setFamlyStatus((prev) => ({ ...prev, status: "error" }));
    } else {
      setBcStatus((prev) => ({ ...prev, status: "error" }));
    }
  };

  const runScrapeOperation = async (
    operation: () => Promise<void>,
    onError?: () => void,
  ) => {
    setIsSyncing(true);
    try {
      await operation();
      await fetchEvents();
    } catch (err) {
      console.error(err);
      onError?.();
    } finally {
      setIsSyncing(false);
    }
  };

  const handleScrapeFamly = async (daysBack: number) => {
    await runScrapeOperation(
      async () => {
        await scrapeFamly(daysBack);
      },
      () => markConnectionError("famly"),
    );
  };

  const handleScrapeBabyConnect = async (daysBack: number = scrapeDaysBack) => {
    await runScrapeOperation(
      async () => {
        await scrapeBabyConnect(daysBack);
      },
      () => markConnectionError("baby_connect"),
    );
  };

  const handleScrapeAll = async () => {
    await runScrapeOperation(
      async () => {
        await scrapeFamly(scrapeDaysBack);
        await scrapeBabyConnect(scrapeDaysBack);
      },
      () => {
        markConnectionError("famly");
        markConnectionError("baby_connect");
      },
    );
  };

  const handleSyncAll = async () => {
    await runScrapeOperation(
      async () => {
        const res = await fetch("/api/sync", { method: "POST" });
        if (!res.ok) {
          throw new Error("Sync failed");
        }
      },
      () => {
        markConnectionError("famly");
        markConnectionError("baby_connect");
      },
    );
  };

  const missingCount = useMemo(
    () => computeMissingCount(famlyEvents, bcEvents),
    [famlyEvents, bcEvents],
  );

  const hasScrapedData = famlyEvents.length > 0 || bcEvents.length > 0;
  const syncDisabled = isSyncing || !hasScrapedData || missingCount === 0;

  const handleCredentialsSaved = async () => {
    await fetchStatus();
  };

  return (
    <div className="app-shell">
      <div className="app-inner">
        <header className="hero">
          <div className="hero__heading">
            <span className="hero__eyebrow">Sync console</span>
            <h1 className="hero__title">Famly → Baby Connect</h1>
            <p className="hero__subtitle">
              Compare timelines, highlight gaps, and sync nursery events with confidence.
            </p>
          </div>
        </header>
        <main className="main-content">
          <div className="controls-bar">
            <div className="controls-bar__group controls-bar__group--left">
              <select
                className="control-select"
                value={scrapeDaysBack}
                onChange={(e) => setScrapeDaysBack(Number(e.target.value))}
              >
                <option value={0}>Last day with entries</option>
                <option value={1}>Last 2 entry days</option>
                <option value={2}>Last 3 entry days</option>
                <option value={3}>Last 4 entry days</option>
              </select>
              <button className="btn btn--secondary" onClick={handleScrapeAll} disabled={isSyncing}>
                Scrape Data
              </button>
            </div>
            <div className="controls-bar__center">
              <button
                className={`btn btn--primary${syncDisabled ? " btn--disabled" : ""}`}
                onClick={handleSyncAll}
                disabled={syncDisabled}
              >
                {isSyncing ? "Syncing..." : "Sync"}
              </button>
            </div>
            <div className="controls-bar__group controls-bar__group--right">
              <button className="btn btn--secondary" onClick={() => setIsSettingsOpen(true)}>
                Settings
              </button>
            </div>
          </div>
          <div className="connection-chips">
            <div
              className={`connection-chip connection-chip--${famlyStatus.status}`}
            >
              <span className="connection-chip__label">Famly</span>
              <span className="connection-chip__status">
                {famlyStatus.status === "ok"
                  ? "Connected"
                  : famlyStatus.status === "error"
                  ? "Error"
                  : "Not connected"}
              </span>
            </div>
            <div className={`connection-chip connection-chip--${bcStatus.status}`}>
              <span className="connection-chip__label">Baby Connect</span>
              <span className="connection-chip__status">
                {bcStatus.status === "ok"
                  ? "Connected"
                  : bcStatus.status === "error"
                  ? "Error"
                  : "Not connected"}
              </span>
            </div>
          </div>
          <EventComparison
            famlyEvents={famlyEvents}
            babyEvents={bcEvents}
            dateFormat={dateFormat}
          />
        </main>
      </div>
      <SettingsDrawer
        open={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        statuses={[famlyStatus, bcStatus]}
        onTestConnection={handleTestConnection}
        onCredentialsSaved={handleCredentialsSaved}
        dateFormat={dateFormat}
        onChangeDateFormat={setDateFormat}
      />
    </div>
  );
};

export default App;
