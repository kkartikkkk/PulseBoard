import { AlertTriangle, CheckCircle, Zap, Clock, TrendingUp } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { resolveAlert } from "../services/api";

const ICONS = {
  latency_spike: Clock,
  error_rate_spike: Zap,
  traffic_spike: TrendingUp,
};

const SEVERITY_COLORS = {
  warning: "border-yellow-600 bg-yellow-900/20",
  critical: "border-red-600 bg-red-900/20",
};

const SEVERITY_BADGE = {
  warning: "bg-yellow-700 text-yellow-100",
  critical: "bg-red-700 text-red-100",
};

export default function AnomalyAlerts({ projectId, alerts, onRefresh }) {
  const handleResolve = async (alertId) => {
    await resolveAlert(projectId, alertId);
    onRefresh();
  };

  if (!alerts || alerts.length === 0) {
    return (
      <div className="bg-gray-800 rounded-xl p-8 border border-gray-700 flex flex-col items-center text-center">
        <CheckCircle className="text-emerald-400 mb-3" size={32} />
        <p className="text-white font-semibold">All clear!</p>
        <p className="text-gray-400 text-sm mt-1">No active anomaly alerts.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => {
        const Icon = ICONS[alert.alert_type] || AlertTriangle;
        const colorClass = SEVERITY_COLORS[alert.severity] || SEVERITY_COLORS.warning;
        const badgeClass = SEVERITY_BADGE[alert.severity] || SEVERITY_BADGE.warning;

        return (
          <div
            key={alert.id}
            className={`rounded-xl p-4 border flex items-start gap-4 ${colorClass}`}
          >
            <Icon
              size={20}
              className={alert.severity === "critical" ? "text-red-400 mt-0.5" : "text-yellow-400 mt-0.5"}
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full uppercase ${badgeClass}`}>
                  {alert.severity}
                </span>
                <span className="text-gray-400 text-xs">
                  {alert.alert_type.replace(/_/g, " ")}
                </span>
                <span className="text-gray-500 text-xs">
                  {formatDistanceToNow(new Date(alert.triggered_at), { addSuffix: true })}
                </span>
              </div>
              <p className="text-white text-sm">{alert.message}</p>
              <p className="text-gray-500 text-xs mt-1">{alert.endpoint}</p>
            </div>
            {!alert.resolved && (
              <button
                onClick={() => handleResolve(alert.id)}
                className="text-gray-400 hover:text-white text-xs border border-gray-600 hover:border-gray-400 px-3 py-1 rounded-lg transition-colors whitespace-nowrap"
              >
                Resolve
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}
