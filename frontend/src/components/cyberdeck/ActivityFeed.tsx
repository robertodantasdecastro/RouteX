import { Activity, Clock3 } from "lucide-react";
import type { RequestLog } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";

export function ActivityFeed({ requests }: { requests: RequestLog[] }) {
  return (
    <section className="activity-feed-panel">
      <header>
        <div>
          <p>Activity</p>
          <strong>Recent requests</strong>
        </div>
        <Activity size={18} />
      </header>
      <div className="activity-feed-list">
        {requests.length === 0 ? (
          <div className="activity-empty">No requests captured yet.</div>
        ) : (
          requests.slice(0, 6).map((request) => (
            <div className="activity-feed-item" key={request.request_id}>
              <Clock3 size={15} />
              <div>
                <strong>{request.model_alias}</strong>
                <span>{request.provider_id ?? "unrouted"} / {request.endpoint}</span>
              </div>
              <StatusBadge status={request.status} />
            </div>
          ))
        )}
      </div>
    </section>
  );
}
