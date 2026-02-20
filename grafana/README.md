# Feniks Grafana Dashboards

This directory contains Grafana dashboard configurations for monitoring Legacy Behavior Guard.

## 📊 Dashboards

### 1. Behavior Guard Overview
**File:** `dashboards/behavior_guard_overview.json`

**Metrics Visualized:**
- Total scenarios and checks
- Pass rate percentage
- Maximum risk score
- Top violations by code
- Check rate over time
- Risk score by scenario
- Scenario duration (p50, p95)
- Checks by environment

**Refresh Rate:** 5 seconds

## 🚀 Quick Start

### Prerequisites
- Grafana 9.0+
- Prometheus 2.x
- Feniks with Prometheus metrics enabled

### Installation

#### Option 1: Manual Import
1. Open Grafana UI (default: http://localhost:3000)
2. Go to **Dashboards > Import**
3. Upload `dashboards/behavior_guard_overview.json`
4. Select Prometheus datasource
5. Click **Import**

#### Option 2: Provisioning (Recommended)
1. Copy datasource configuration:
   ```bash
   sudo cp provisioning/datasources/prometheus.yml /etc/grafana/provisioning/datasources/
   ```

2. Copy dashboard configuration:
   ```bash
   sudo cp dashboards/behavior_guard_overview.json /etc/grafana/provisioning/dashboards/
   ```

3. Restart Grafana:
   ```bash
   sudo systemctl restart grafana-server
   ```

4. Access dashboard at: http://localhost:3000/d/feniks-behavior-guard

## 📈 Metrics Reference

Feniks exports the following Prometheus metrics for Legacy Behavior Guard:

### Scenario Metrics
- `feniks_behavior_scenarios_total` - Total number of defined scenarios
- `feniks_behavior_scenarios_by_category{category}` - Scenarios by category (api/ui/cli)

### Check Metrics
- `feniks_behavior_checks_total` - Total behavior checks executed
- `feniks_behavior_checks_passed` - Total passed checks
- `feniks_behavior_checks_failed` - Total failed checks
- `feniks_behavior_checks_by_environment{environment}` - Checks by environment (legacy/candidate/staging/production)

### Risk Metrics
- `feniks_behavior_max_risk_score` - Maximum risk score across all checks (0.0-1.0)
- `feniks_behavior_risk_score_by_scenario{scenario_id}` - Risk score per scenario
- `feniks_behavior_avg_risk_score` - Average risk score

### Violation Metrics
- `feniks_behavior_violations_total` - Total violations detected
- `feniks_behavior_violations_by_code{code}` - Violations by type code
- `feniks_behavior_violations_by_severity{severity}` - Violations by severity (critical/high/medium/low)

### Performance Metrics
- `feniks_behavior_duration_ms_bucket` - Scenario execution duration histogram
- `feniks_behavior_duration_ms_sum` - Total duration sum
- `feniks_behavior_duration_ms_count` - Duration observation count

## 🔧 Configuration

### Enable Metrics in Feniks

Update `feniks` configuration:

```python
# config/settings.py
metrics_enabled = True
metrics_export_path = "/metrics/prometheus"
```

### Prometheus Configuration

Add Feniks scrape target to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'feniks'
    scrape_interval: 5s
    static_configs:
      - targets: ['localhost:8000']  # Feniks API port
    metrics_path: '/metrics/prometheus'
```

## 📊 Dashboard Panels

### 1. Total Scenarios
- **Type:** Gauge
- **Query:** `feniks_behavior_scenarios_total`
- **Description:** Total number of defined behavior scenarios

### 2. Total Checks
- **Type:** Gauge
- **Query:** `feniks_behavior_checks_total`
- **Description:** Total behavior checks executed

### 3. Pass Rate
- **Type:** Gauge (%)
- **Query:** `(feniks_behavior_checks_passed / feniks_behavior_checks_total) * 100`
- **Thresholds:**
  - 🔴 Red: < 70%
  - 🟡 Yellow: 70-90%
  - 🟢 Green: > 90%

### 4. Max Risk Score
- **Type:** Gauge (0.0-1.0)
- **Query:** `feniks_behavior_max_risk_score`
- **Thresholds:**
  - 🟢 Green: < 0.5
  - 🟡 Yellow: 0.5-0.7
  - 🔴 Red: > 0.7

### 5. Top Violations
- **Type:** Table
- **Query:** `topk(10, feniks_behavior_violations_by_code)`
- **Description:** Top 10 violation types by count

### 6. Check Rate Over Time
- **Type:** Time Series
- **Query:** `rate(feniks_behavior_checks_total[5m])`
- **Description:** Checks per second over time

### 7. Risk Score by Scenario
- **Type:** Time Series
- **Query:** `feniks_behavior_risk_score_by_scenario`
- **Description:** Risk score trends per scenario
- **Legend:** Shows mean and max values

### 8. Scenario Duration (p50, p95)
- **Type:** Time Series (Bar)
- **Queries:**
  - `histogram_quantile(0.95, feniks_behavior_duration_ms_bucket)` - p95
  - `histogram_quantile(0.50, feniks_behavior_duration_ms_bucket)` - p50
- **Description:** Duration percentiles for performance monitoring

### 9. Checks by Environment
- **Type:** Pie Chart (Donut)
- **Query:** `feniks_behavior_checks_by_environment`
- **Description:** Distribution of checks across environments

## 🎨 Customization

### Adding Custom Panels

1. Edit dashboard JSON file
2. Add new panel to `panels` array:
   ```json
   {
     "id": 10,
     "title": "My Custom Panel",
     "type": "graph",
     "targets": [
       {
         "expr": "my_custom_query",
         "refId": "A"
       }
     ]
   }
   ```

### Adjusting Thresholds

Modify `thresholds` in panel configuration:
```json
"thresholds": {
  "mode": "absolute",
  "steps": [
    {"color": "green", "value": null},
    {"color": "yellow", "value": 0.5},
    {"color": "red", "value": 0.7}
  ]
}
```

## 🐛 Troubleshooting

### No Data in Dashboard
1. Verify Prometheus is scraping Feniks:
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```

2. Check Feniks metrics endpoint:
   ```bash
   curl http://localhost:8000/metrics/prometheus
   ```

3. Verify datasource connection in Grafana

### Slow Dashboard
1. Reduce refresh rate (Settings > Time options)
2. Adjust time range (default: 6 hours)
3. Optimize PromQL queries with rate functions

### Missing Metrics
1. Ensure metrics are enabled in Feniks settings
2. Run behavior checks to generate metrics
3. Check Prometheus scrape errors

## 📚 Additional Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Feniks Metrics Documentation](../../docs/METRICS.md)

## 🤝 Contributing

To add new dashboards:
1. Create dashboard in Grafana UI
2. Export JSON: Settings > JSON Model
3. Save to `dashboards/` directory
4. Update this README with metrics and panels
5. Submit pull request

---

**Last Updated:** 2025-11-26
**Dashboard Version:** 1.0.0
