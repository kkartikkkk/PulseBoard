import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, BarChart, Bar
} from "recharts";
import { format } from "date-fns";

function formatHour(iso) {
  try {
    return format(new Date(iso), "HH:mm");
  } catch {
    return iso;
  }
}

function prepareChartData(metrics) {
  // Group by hour bucket, sum across endpoints
  const buckets = {};
  for (const m of metrics) {
    const key = m.hour_bucket;
    if (!buckets[key]) {
      buckets[key] = {
        hour: formatHour(key),
        total_requests: 0,
        error_count: 0,
        avg_latency_ms: 0,
        _latency_sum: 0,
        _req_count: 0,
      };
    }
    buckets[key].total_requests += m.total_requests;
    buckets[key].error_count += m.error_count;
    buckets[key]._latency_sum += m.avg_latency_ms * m.total_requests;
    buckets[key]._req_count += m.total_requests;
  }

  return Object.values(buckets)
    .map((b) => ({
      ...b,
      avg_latency_ms: b._req_count > 0 ? Math.round(b._latency_sum / b._req_count) : 0,
      error_rate: b.total_requests > 0
        ? parseFloat(((b.error_count / b.total_requests) * 100).toFixed(2))
        : 0,
    }))
    .reverse();
}

export default function MetricsChart({ metrics }) {
  const data = prepareChartData(metrics || []);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Requests over time */}
      <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
        <h3 className="text-white font-semibold mb-4">Requests / Hour</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="hour" stroke="#6B7280" tick={{ fontSize: 11 }} />
            <YAxis stroke="#6B7280" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ backgroundColor: "#1F2937", border: "1px solid #374151", borderRadius: 8 }}
              labelStyle={{ color: "#E5E7EB" }}
            />
            <Bar dataKey="total_requests" fill="#6366F1" name="Requests" radius={[4, 4, 0, 0]} />
            <Bar dataKey="error_count" fill="#EF4444" name="Errors" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Latency over time */}
      <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
        <h3 className="text-white font-semibold mb-4">Avg Latency (ms)</h3>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="hour" stroke="#6B7280" tick={{ fontSize: 11 }} />
            <YAxis stroke="#6B7280" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ backgroundColor: "#1F2937", border: "1px solid #374151", borderRadius: 8 }}
              labelStyle={{ color: "#E5E7EB" }}
            />
            <Line
              type="monotone"
              dataKey="avg_latency_ms"
              stroke="#10B981"
              strokeWidth={2}
              dot={false}
              name="Avg Latency (ms)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Error rate */}
      <div className="bg-gray-800 rounded-xl p-5 border border-gray-700 lg:col-span-2">
        <h3 className="text-white font-semibold mb-4">Error Rate (%)</h3>
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="hour" stroke="#6B7280" tick={{ fontSize: 11 }} />
            <YAxis stroke="#6B7280" tick={{ fontSize: 11 }} unit="%" />
            <Tooltip
              contentStyle={{ backgroundColor: "#1F2937", border: "1px solid #374151", borderRadius: 8 }}
              labelStyle={{ color: "#E5E7EB" }}
              formatter={(v) => [`${v}%`, "Error Rate"]}
            />
            <Line
              type="monotone"
              dataKey="error_rate"
              stroke="#F59E0B"
              strokeWidth={2}
              dot={false}
              name="Error Rate"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
