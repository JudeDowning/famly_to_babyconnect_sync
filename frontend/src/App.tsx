import React, { useEffect, useState } from "react";
import {
  ConnectionStatus,
  NormalisedEvent,
  ServiceName,
} from "./types";
import { ConnectionCard } from "./components/ConnectionCard";
import { EventsColumn } from "./components/EventsColumn";
import { SyncControls } from "./components/SyncControls";

const App: React.FC = () => {
  const [famlyStatus, setFamlyStatus] = useState<ConnectionStatus>({
    service: "famly",
    email: null,
    status: "idle",
  });
  const [bcStatus, setBcStatus] = useState<ConnectionStatus>({
    service: "baby_connect",
    email: null,
    status: "idle",
  });
  const [famlyEvents, setFamlyEvents] = useState<NormalisedEvent[]>([]);
  const [bcEvents, setBcEvents] = useState<NormalisedEvent[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);

  const fetchStatus = async () => {
    const res = await fetch("/api/status");
    const data = await res.json();
    setFamlyStatus((prev) => ({
      ...prev,
      status: data.famly.has_credentials ? "ok" : "idle",
      email: prev.email, // credentials endpoint not wired yet
    }));
    setBcStatus((prev) => ({
      ...prev,
      status: data.baby_connect.has_credentials ? "ok" : "idle",
      email: prev.email,
    }));
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

  const handleScrapeFamly = async () => {
    setIsSyncing(true);
    try {
      await fetch("/api/scrape/famly", { method: "POST" });
      await fetchEvents();
    } finally {
      setIsSyncing(false);
    }
  };

  const handleSyncAll = async () => {
    setIsSyncing(true);
    try {
      await fetch("/api/sync", { method: "POST" });
      await fetchEvents();
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="min-h-screen p-4">
      {/* Connection row */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <ConnectionCard status={famlyStatus} onTestConnection={handleTestConnection} />
        <SyncControls
          isSyncing={isSyncing}
          onSyncAll={handleSyncAll}
          onScrapeFamly={handleScrapeFamly}
        />
        <ConnectionCard status={bcStatus} onTestConnection={handleTestConnection} />
      </div>

      {/* Events lists */}
      <div className="grid grid-cols-3 gap-4">
        <EventsColumn title="Famly events" events={famlyEvents} />
        <div />
        <EventsColumn title="Baby Connect events" events={bcEvents} />
      </div>
    </div>
  );
};

export default App;
