import React from "react";
import { NormalisedEvent } from "../types";

interface Props {
  title: string;
  events: NormalisedEvent[];
}

export const EventsColumn: React.FC<Props> = ({ title, events }) => {
  return (
    <div>
      <h3 className="font-semibold mb-2">{title}</h3>
      <div className="space-y-2 max-h-[60vh] overflow-auto">
        {events.map((ev) => (
          <div
            key={ev.id}
            className={`p-2 text-sm rounded border ${
              ev.matched ? "bg-green-50 border-green-300" : "bg-white"
            }`}
          >
            <div className="font-medium">
              {ev.child_name} – {ev.event_type}
            </div>
            <div className="text-xs">{ev.start_time_utc}</div>
            {ev.summary && <div className="text-xs">{ev.summary}</div>}
          </div>
        ))}
      </div>
    </div>
  );
};
