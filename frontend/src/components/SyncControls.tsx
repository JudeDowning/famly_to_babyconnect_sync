import React from "react";

interface Props {
  isSyncing: boolean;
  onSyncAll: () => void;
  onScrapeFamly: () => void;
}

export const SyncControls: React.FC<Props> = ({ isSyncing, onSyncAll, onScrapeFamly }) => {
  return (
    <div className="flex flex-col items-center justify-center space-y-3">
      <button
        className="px-4 py-2 rounded-xl border shadow text-sm"
        onClick={onScrapeFamly}
        disabled={isSyncing}
      >
        Scrape Famly
      </button>
      <button
        className="px-4 py-2 rounded-xl border shadow text-sm"
        onClick={onSyncAll}
        disabled={isSyncing}
      >
        {isSyncing ? "Syncing…" : "Sync All"}
      </button>
    </div>
  );
};
