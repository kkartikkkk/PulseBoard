"""
Anomaly Detection Service
Uses Z-score and IQR statistical methods to detect:
  - Latency spikes
  - Error rate spikes
  - Traffic spikes

No heavy ML framework needed — pure Python statistics.
This is intentionally simple but explains well in interviews.
"""

import statistics
from typing import List, Dict, Any


def z_score(value: float, data: List[float]) -> float:
    """Standard Z-score: how many std deviations from the mean."""
    if len(data) < 2:
        return 0.0
    mean = statistics.mean(data)
    std = statistics.stdev(data)
    if std == 0:
        return 0.0
    return (value - mean) / std


def detect_latency_spike(current_latency: float, historical_latencies: List[float], threshold: float = 2.5) -> Dict[str, Any]:
    """
    Flag if current avg latency is more than `threshold` std deviations above historical mean.
    Returns a dict with is_anomaly, severity, and z_score.
    """
    if len(historical_latencies) < 5:
        return {"is_anomaly": False, "z": 0.0}

    z = z_score(current_latency, historical_latencies)
    if z > threshold * 2:
        return {"is_anomaly": True, "severity": "critical", "z": round(z, 2)}
    elif z > threshold:
        return {"is_anomaly": True, "severity": "warning", "z": round(z, 2)}
    return {"is_anomaly": False, "z": round(z, 2)}


def detect_error_rate_spike(current_error_rate: float, historical_error_rates: List[float], threshold: float = 2.5) -> Dict[str, Any]:
    """
    Flag if current error rate is unusually high compared to history.
    Also flags if absolute error rate crosses 10% (hard threshold).
    """
    if current_error_rate >= 0.10:
        return {"is_anomaly": True, "severity": "critical", "z": None, "reason": "error_rate > 10%"}

    if len(historical_error_rates) < 5:
        return {"is_anomaly": False, "z": 0.0}

    z = z_score(current_error_rate, historical_error_rates)
    if z > threshold * 2:
        return {"is_anomaly": True, "severity": "critical", "z": round(z, 2)}
    elif z > threshold:
        return {"is_anomaly": True, "severity": "warning", "z": round(z, 2)}
    return {"is_anomaly": False, "z": round(z, 2)}


def detect_traffic_spike(current_requests: int, historical_requests: List[int], threshold: float = 3.0) -> Dict[str, Any]:
    """
    Flag sudden traffic bursts (could be a DDoS or viral event).
    """
    if len(historical_requests) < 5:
        return {"is_anomaly": False, "z": 0.0}

    z = z_score(current_requests, [float(r) for r in historical_requests])
    if z > threshold * 2:
        return {"is_anomaly": True, "severity": "critical", "z": round(z, 2)}
    elif z > threshold:
        return {"is_anomaly": True, "severity": "warning", "z": round(z, 2)}
    return {"is_anomaly": False, "z": round(z, 2)}


def run_all_checks(
    endpoint: str,
    current_latency: float,
    current_error_rate: float,
    current_requests: int,
    historical_latencies: List[float],
    historical_error_rates: List[float],
    historical_requests: List[int],
) -> List[Dict[str, Any]]:
    """
    Run all anomaly checks for an endpoint and return a list of triggered alerts.
    Each alert has: endpoint, alert_type, message, severity.
    """
    alerts = []

    lat = detect_latency_spike(current_latency, historical_latencies)
    if lat["is_anomaly"]:
        alerts.append({
            "endpoint": endpoint,
            "alert_type": "latency_spike",
            "message": f"Latency spike detected on {endpoint}: {current_latency:.1f}ms (z={lat['z']})",
            "severity": lat["severity"],
        })

    err = detect_error_rate_spike(current_error_rate, historical_error_rates)
    if err["is_anomaly"]:
        alerts.append({
            "endpoint": endpoint,
            "alert_type": "error_rate_spike",
            "message": f"Error rate spike on {endpoint}: {current_error_rate*100:.1f}%",
            "severity": err["severity"],
        })

    traffic = detect_traffic_spike(current_requests, historical_requests)
    if traffic["is_anomaly"]:
        alerts.append({
            "endpoint": endpoint,
            "alert_type": "traffic_spike",
            "message": f"Traffic spike on {endpoint}: {current_requests} requests this hour (z={traffic['z']})",
            "severity": traffic["severity"],
        })

    return alerts
