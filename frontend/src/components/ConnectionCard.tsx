import React from "react";
import { ConnectionStatus, ServiceName } from "../types";

interface Props {
  status: ConnectionStatus;
  onTestConnection: (service: ServiceName) => void;
}

const bgClass = (status: ConnectionStatus["status"]) => {
  switch (status) {
    case "ok":
      return "bg-green-200";
    case "error":
      return "bg-red-200";
    default:
      return "bg-gray-100";
  }
};

export const ConnectionCard: React.FC<Props> = ({ status, onTestConnection }) => {
  const label = status.service === "famly" ? "Famly (Source)" : "Baby Connect (Target)";
  return (
    <div className={`rounded-xl p-4 shadow ${bgClass(status.status)}`}>
      <h2 className="font-semibold text-lg mb-2">{label}</h2>
      <p className="text-sm mb-1">Email: {status.email || "Not set"}</p>
      {status.message && <p className="text-xs">{status.message}</p>}
      <button
        className="mt-3 px-3 py-1 rounded border text-sm"
        onClick={() => onTestConnection(status.service)}
      >
        Test connection
      </button>
    </div>
  );
};
