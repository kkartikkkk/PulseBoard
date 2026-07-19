import { Activity, AlertTriangle, Clock, Zap } from "lucide-react";

function Card({ label, value, sub, icon: Icon, color }) {
  return (
    <div className="bg-gray-800 rounded-xl p-5 border border-gray-700 flex items-start gap-4">
      <div className={`p-2 rounded-lg ${color}`}>
        <Icon size={20} className="text-white" />
      </div>
      <div>
        <p className="text-gray-400 text-xs uppercase tracking-wider mb-1">{label}</p>
        <p className="text-white text-2xl font-bold">{value ?? "—"}</p>
        {sub && <p className="text-gray-500 text-xs mt-1">{sub}</p>}
      </div>
    </div>
  );
}

export default function SummaryCards({ summary, live }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <Card
        label="Requests (24h)"
        value={summary?.total_requests_24h?.toLocaleString()}
        sub={live ? `${live.total_requests_5m} in last 5m` : null}
        icon={Activity}
        color="bg-indigo-600"
      />
      <Card
        label="Avg Latency"
        value={summary ? `${summary.avg_latency_ms}ms` : null}
        sub={live ? `Live: ${live.avg_latency_ms}ms` : null}
        icon={Clock}
        color="bg-emerald-600"
      />
      <Card
        label="Error Rate"
        value={summary ? `${(summary.error_rate_24h * 100).toFixed(2)}%` : null}
        sub={`${summary?.total_errors_24h ?? 0} errors`}
        icon={Zap}
        color={summary?.error_rate_24h > 0.05 ? "bg-red-600" : "bg-yellow-600"}
      />
      <Card
        label="Open Alerts"
        value={summary?.open_alerts ?? 0}
        sub={summary?.top_endpoint ? `Top: ${summary.top_endpoint}` : null}
        icon={AlertTriangle}
        color={summary?.open_alerts > 0 ? "bg-orange-600" : "bg-gray-600"}
      />
    </div>
  );
}
