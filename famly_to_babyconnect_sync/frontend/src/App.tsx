import React, { useCallback, useEffect, useRef, useState } from "react";
import { ConnectionStatus, NormalisedEvent, ServiceName, SyncPreferences } from "./types";
import { SettingsDrawer } from "./components/SettingsDrawer";
import { EventComparison } from "./components/EventComparison";
import { ProgressOverlay } from "./components/ProgressOverlay";
import { SyncToast } from "./components/SyncToast";
import {
  syncEventsToBabyConnect,
  fetchMissingEventIds,
  syncAllMissingEvents,
  fetchSyncPreferences,
} from "./api";

type DateFormat = "weekday-mon-dd" | "weekday-dd-mon";

type ProgressState = {
  visible: boolean;
  label: string;
  currentStep: number;
  totalSteps: number;
  famlyTarget: number;
  babyTarget: number;
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
  const [missingEventIds, setMissingEventIds] = useState<number[]>([]);
  const [syncPreferences, setSyncPreferences] = useState<SyncPreferences>({ include_types: [] });
  const [isSyncing, setIsSyncing] = useState(false);
  const [scrapeDaysBack, setScrapeDaysBack] = useState(0);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [dateFormat, setDateFormat] = useState<DateFormat>("weekday-mon-dd");
  const [progress, setProgress] = useState<ProgressState>({
    visible: false,
    label: "",
    currentStep: 0,
    totalSteps: 0,
    famlyTarget: 0,
    babyTarget: 0,
  });
  const [syncingEventId, setSyncingEventId] = useState<number | null>(null);
  const [syncAllInFlight, setSyncAllInFlight] = useState(false);
  const [showMissingOnly, setShowMissingOnly] = useState(false);
  const pollersRef = useRef<{ [key in ServiceName]?: () => void }>({});

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

  const loadMissingEventIds = useCallback(async () => {
    try {
      const ids = await fetchMissingEventIds();
      setMissingEventIds(ids);
    } catch (error) {
      console.error("Failed to load missing events", error);
      setMissingEventIds([]);
    }
  }, []);

  const loadSyncPreferences = useCallback(async () => {
    try {
      const prefs = await fetchSyncPreferences();
      setSyncPreferences(prefs);
    } catch (error) {
      console.error("Failed to load sync preferences", error);
    }
  }, []);

  const fetchEvents = async () => {
    const [famlyRes, bcRes] = await Promise.all([
      fetch("/api/events?source=famly"),
      fetch("/api/events?source=baby_connect"),
    ]);
    const famlyData = await famlyRes.json();
    const bcData = await bcRes.json();
    setFamlyEvents(famlyData);
    setBcEvents(bcData);
    await loadMissingEventIds();
  };

  useEffect(() => {
    fetchStatus();
    fetchEvents();
    loadSyncPreferences();
  }, [loadSyncPreferences]);

  const handleTestConnection = async (service: ServiceName) => {
    // For now, just ping /api/status to simulate an update.
    await fetchStatus();
  };

  const scrapeFamly = async (daysBack: number) => {
    const res = await fetch(`/api/scrape/famly?days_back=${daysBack}`, { method: "POST" });
    if (!res.ok) {
      throw new Error("Failed to scrape Famly");
    }
    const data = await res.json();
    return typeof data.scraped_count === "number" ? data.scraped_count : 0;
  };

  const scrapeBabyConnect = async (daysBack: number) => {
    const res = await fetch(`/api/scrape/baby_connect?days_back=${daysBack}`, {
      method: "POST",
    });
    if (!res.ok) {
      throw new Error("Failed to scrape Baby Connect");
    }
    const data = await res.json();
    return typeof data.scraped_count === "number" ? data.scraped_count : 0;
  };

  const startProgressPolling = (service: ServiceName, baseline: number) => {
    let stopped = false;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    const source = service === "famly" ? "famly" : "baby_connect";

    const poll = async () => {
      if (stopped) return;
      try {
        const res = await fetch(`/api/events?source=${source}`);
        if (!res.ok) {
          throw new Error("poll failed");
        }
        const data = await res.json();
        const count = Array.isArray(data) ? data.length : 0;
        const diff = Math.max(0, count - baseline);
        setProgress((prev) => {
          if (!prev.visible) return prev;
          if (service === "famly") {
            return { ...prev, famlyTarget: diff };
          }
          return { ...prev, babyTarget: diff };
        });
      } catch (error) {
        console.debug("Progress polling error", error);
      } finally {
        if (!stopped) {
          timeoutId = setTimeout(poll, 700);
        }
      }
    };

    const stop = () => {
      stopped = true;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      if (pollersRef.current[service] === stop) {
        delete pollersRef.current[service];
      }
    };

    poll();
    pollersRef.current[service] = stop;
    return stop;
  };

  const stopPollers = (service?: ServiceName) => {
    if (service) {
      pollersRef.current[service]?.();
      delete pollersRef.current[service];
      return;
    }
    (Object.keys(pollersRef.current) as ServiceName[]).forEach((key) => {
      pollersRef.current[key]?.();
      delete pollersRef.current[key];
    });
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
    stopPollers();
    setProgress({
      visible: true,
      label: "Scraping FamlyÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦",
      currentStep: 0,
      totalSteps: 1,
      famlyTarget: 0,
      babyTarget: 0,
    });
    const stopFamlyPoll = startProgressPolling("famly", famlyEvents.length);
    await runScrapeOperation(
      async () => {
        const count = await scrapeFamly(daysBack);
        setProgress((prev) => ({
          ...prev,
          currentStep: 1,
          famlyTarget: count,
        }));
      },
      () => markConnectionError("famly"),
    );
    stopFamlyPoll();
    await new Promise((resolve) => setTimeout(resolve, 500));
    setProgress((prev) => ({ ...prev, visible: false }));
  };

  const handleScrapeBabyConnect = async (daysBack: number = scrapeDaysBack) => {
    stopPollers();
    setProgress({
      visible: true,
      label: "Scraping Baby ConnectÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦",
      currentStep: 0,
      totalSteps: 1,
      famlyTarget: 0,
      babyTarget: 0,
    });
    const stopBabyPoll = startProgressPolling("baby_connect", bcEvents.length);
    await runScrapeOperation(
      async () => {
        const count = await scrapeBabyConnect(daysBack);
        setProgress((prev) => ({
          ...prev,
          currentStep: 1,
          babyTarget: count,
        }));
      },
      () => markConnectionError("baby_connect"),
    );
    stopBabyPoll();
    await new Promise((resolve) => setTimeout(resolve, 500));
    setProgress((prev) => ({ ...prev, visible: false }));
  };

  const handleScrapeAll = async () => {
    stopPollers();
    setProgress({
      visible: true,
      label: "Scraping FamlyÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦",
      currentStep: 0,
      totalSteps: 2,
      famlyTarget: 0,
      babyTarget: 0,
    });
    const stopFamlyPoll = startProgressPolling("famly", famlyEvents.length);
    await runScrapeOperation(
      async () => {
        const famlyCount = await scrapeFamly(scrapeDaysBack);
        setProgress((prev) => ({
          ...prev,
          currentStep: 1,
          label: "Scraping Baby ConnectÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦",
          famlyTarget: famlyCount,
        }));
        stopFamlyPoll();
        const stopBabyPoll = startProgressPolling("baby_connect", bcEvents.length);
        const babyCount = await scrapeBabyConnect(scrapeDaysBack);
        setProgress((prev) => ({
          ...prev,
          currentStep: 2,
          babyTarget: babyCount,
        }));
        stopBabyPoll();
      },
      () => {
        markConnectionError("famly");
        markConnectionError("baby_connect");
      },
    );
    await new Promise((resolve) => setTimeout(resolve, 500));
    setProgress((prev) => ({ ...prev, visible: false }));
  };

  const handleSyncAll = async () => {
    if (!missingEventIds.length) return;
    setSyncAllInFlight(true);
    try {
      await syncAllMissingEvents();
      await fetchEvents();
    } catch (err) {
      console.error(err);
      alert(err instanceof Error ? err.message : "Failed to sync entries");
      markConnectionError("baby_connect");
    } finally {
      setSyncAllInFlight(false);
    }
  };

  const handleSyncSingleEvent = async (eventId: number) => {
    setSyncingEventId(eventId);
    try {
      await syncEventsToBabyConnect([eventId]);
      await fetchEvents();
    } catch (err) {
      console.error(err);
      alert(err instanceof Error ? err.message : "Failed to sync entry");
    } finally {
      setSyncingEventId(null);
    }
  };

  const handleSyncPreferencesSaved = useCallback(
    async (prefs: SyncPreferences) => {
      setSyncPreferences(prefs);
      await loadMissingEventIds();
    },
    [loadMissingEventIds],
  );

  const missingCount = missingEventIds.length;

  const hasScrapedData = famlyEvents.length > 0 || bcEvents.length > 0;
  const syncDisabled =
    isSyncing || syncAllInFlight || !hasScrapedData || missingCount === 0;

  const handleCredentialsSaved = async () => {
    await fetchStatus();
  };

  return (
    <div className="app-shell">
      <div className="app-inner">
        <header className="hero hero--compact">
          <div>
            <h1 className="hero__title">Famly &rarr; Baby Connect</h1>
            <p className="hero__subtitle">
              Compare timelines, spot differences, and push missing events in a single view.
            </p>
          </div>
          <div className="hero__actions">
            <button className="btn btn--secondary" onClick={() => setIsSettingsOpen(true)}>
              Settings
            </button>
          </div>
        </header>
        <main className="main-content">
          <div className="workflow-steps">
            <div className="workflow-step">
              <p className="workflow-step__label">Step 1</p>
              <h3 className="workflow-step__title">Scrape latest data</h3>
              <p className="workflow-step__body">
                Choose how many recent entry days to include, then run the scrape to pull fresh
                Famly and Baby Connect records.
              </p>
            </div>
            <div className="workflow-arrow">→</div>
            <div className="workflow-step">
              <p className="workflow-step__label">Step 2</p>
              <h3 className="workflow-step__title">Compare timelines</h3>
              <p className="workflow-step__body">
                Review Famly vs Baby Connect entries, filter for missing ones, and inspect the icons
                for per-event details.
              </p>
            </div>
            <div className="workflow-arrow">→</div>
            <div className="workflow-step">
              <p className="workflow-step__label">Step 3</p>
              <h3 className="workflow-step__title">Sync anything missing</h3>
              <p className="workflow-step__body">
                Use the Sync All action or the per-event arrows to push outstanding entries into
                Baby Connect with one click.
              </p>
            </div>
          </div>
          <div className="connection-chips">
            <div className={`connection-chip connection-chip--${famlyStatus.status}`}>
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
            controlsSlot={
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
                    {isSyncing ? "Syncing..." : "Sync All"}
                  </button>
                </div>
                <div className="controls-bar__group controls-bar__group--right">
                  <div className="controls-bar__right-buttons">
                    <button
                      type="button"
                      className="btn btn--secondary"
                      onClick={() => setShowMissingOnly((prev) => !prev)}
                    >
                      {showMissingOnly ? "Show all entries" : "Show only missing"}
                    </button>
                  </div>
                </div>
              </div>
            }
            famlyEvents={famlyEvents}
            babyEvents={bcEvents}
            dateFormat={dateFormat}
            onSyncEvent={handleSyncSingleEvent}
            syncingEventId={syncingEventId}
            isBulkSyncing={syncAllInFlight}
            showMissingOnly={showMissingOnly}
            onToggleMissing={() => setShowMissingOnly((prev) => !prev)}
          />
        </main>
      </div>
      <SettingsDrawer
        open={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        statuses={[famlyStatus, bcStatus]}
        onTestConnection={handleTestConnection}
        onCredentialsSaved={handleCredentialsSaved}
        onSyncPreferencesSaved={handleSyncPreferencesSaved}
        syncPreferences={syncPreferences}
        dateFormat={dateFormat}
        onChangeDateFormat={setDateFormat}
      />
      <ProgressOverlay progress={progress} />
      <SyncToast mode={syncAllInFlight ? "bulk" : syncingEventId ? "single" : null} />
    </div>
  );
};

export default App;



