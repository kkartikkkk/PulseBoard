import { useState, useEffect, useRef, useCallback } from "react";
import { getSummary, getMetrics, getAlerts, createLiveSocket } from "../services/api";
import SummaryCards from "./SummaryCards";
import MetricsChart from "./MetricsChart";
import AnomalyAlerts from "./AnomalyAlerts";
import { RefreshCw, Wifi } from "lucide-react";

export default function Dashboard({ project }) {
  const [summary, setSummary] = useState(null);
  const [metrics, setMetrics] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [liveData, setLiveData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isLive, setIsLive] = useState(false);
  const [hours, setHours] = useState(24);
  const wsRef = useRef(null);

  const fetchAll = useCallback(async () => {
    try {
      const [s, m, a] = await Promise.all([
        getSummary(project.id),
        getMetrics(project.id, hours),
        getAlerts(project.id, false),
      ]);
      setSummary(s.data);
      setMetrics(m.data);
      setAlerts(a.data);
    } catch (err) {
      console.error("Failed to fetch dashboard data", err);
    } finally {
      setLoading(false);
    }
  }, [project.id, hours]);

  // Auto-refresh every 30s
  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 30_000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  // WebSocket live feed
  useEffect(() => {
    const ws = createLiveSocket(project.id, (data) => {
      setLiveData(data);
      setIsLive(true);
    });
    wsRef.current = ws;
    return () => ws.close();
  }, [project.id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-400" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-white text-xl font-bold">{project.name}</h1>
          <p className="text-gray-400 text-sm mt-0.5">API Key: <code className="text-indigo-400">{project.api_key}</code></p>
        </div>
        <div className="flex items-center gap-3">
          {isLive && (
            <div className="flex items-center gap-1.5 text-emerald-400 text-xs">
              <Wifi size={14} />
              <span>Live</span>
              <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            </div>
          )}
          <select
            value={hours}
            onChange={(e) => setHours(Number(e.target.value))}
            className="bg-gray-700 text-gray-200 text-sm rounded-lg px-3 py-1.5 border border-gray-600 focus:outline-none"
          >
            <option value={6}>Last 6h</option>
            <option value={24}>Last 24h</option>
            <option value={72}>Last 3d</option>
            <option value={168}>Last 7d</option>
          </select>
          <button
            onClick={fetchAll}
            className="text-gray-400 hover:text-white transition-colors p-1.5"
            title="Refresh"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <SummaryCards summary={summary} live={liveData} />

      {/* Charts */}
      <MetricsChart metrics={metrics} />

      {/* Alerts */}
      <div>
        <h2 className="text-white font-semibold mb-3 flex items-center gap-2">
          Anomaly Alerts
          {alerts.filter((a) => !a.resolved).length > 0 && (
            <span className="bg-red-600 text-white text-xs font-bold px-2 py-0.5 rounded-full">
              {alerts.filter((a) => !a.resolved).length}
            </span>
          )}
        </h2>
        <AnomalyAlerts
          projectId={project.id}
          alerts={alerts.filter((a) => !a.resolved)}
          onRefresh={fetchAll}
        />
      </div>
    </div>
  );
}
