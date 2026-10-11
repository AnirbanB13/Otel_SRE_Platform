# Resilient Microservices Observability Platform with OpenTelemetry & SLO Alerting

An enterprise-grade, polyglot observability pipeline built for Site Reliability Engineering (SRE). This project moves beyond basic server monitoring by implementing unified OpenTelemetry data collection, trace-to-log correlation, and autom ated multi-window, multi-burn-rate error budget alerting.

## 7' 🏗️ Architecture & Telemetry Flow

The platform centralizes all telemetry signals (Metrics, Logs, and Traces) through an OpenTelemetry Collector before dispatching them to specialized storage backends.

```
  [ FastAPI Application ]
           │
           │ (OTLP gRPC / HTTP) f
           ▼
  ┌────────────────────────────────────────┐
  │         OpenTelemetry Collector        │
  └────┬──────────────┬──────────────┬─────┘
       │              │              │
       ▼ (Metrics)    ▼ (Traces)     ▼ (Logs)
  [Prometheus]     [Tempo]        [Loki]
       │              │              │
       └──────────────┴──────────────┘
                      │
                      ▼
               [ Grafana UI ]

```

## 🚀 Tech Stack

* **Instrumentation & Collection:** OpenTelemetry SDK & OTel Collector Contrib

* **Application Framework:** Python FastAPI (Auto-instrumented with W3C Trace Context propagation)

* **Metrics & Alerting:** Prometheus & Prometheus Alertmanager (connected to Discord/Slack webhooks)

* **Logs Aggregation:** Grafana Loki (with automated trace ID injection)

* **Distributed Tracing:** Grafana Tempo

* **Visualization:** Grafana

* **Containerization:** Docker & Docker Compose

## 🛠️ Getting Started Locally

### Prerequisites

* Docker & Docker Compose installed on your machine.

* Python 3.9+ installed for running the demo microservice.

### 1. Clone the Repository

```
git clone https://github.com/your-username/otel-sre-observability-platform.git
cd otel-sre-observability-platform

```

### 2. Configure Chat Webhooks (Optional)

Open `alertmanager.yml` and insert your Discord or Slack webhook URL if you wish to receive real-time SRE alert notifications.

### 3. Spin Up Infrastructure Stack

```
docker compose up -d

```

Verify that all containers (`otel-collector`, `prometheus`, `loki`, `tempo`, `grafana`, `alertmanager`) are healthy.

### 4. Run the Instrumented Application

Install dependencies and start the FastAPI server:

```
pip install fastapi uvicorn opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-fastapi
uvicorn app:app --host 0.0.0.0 --port 8000

```

## 📊 SRE Methodology & Error Budget Burn Rates

Rather than triggering noisy alerts on single random errors, this project implements the Google SRE workbook standard: **Multi-Window, Multi-Burn-Rate Alerts**.

* **SLO Target:** $99.9\%$ availability over a 30-day window (Allowing an error budget of $\approx 43$ minutes).

* **Fast Burn Rate Alert (`>14.4x`):** PagerDuty/Webhook triggers immediately if $\ge 2\%$ of the monthly error budget is consumed within 1 hour.

* **Slow Burn Rate Alert (`>6x`):** Warning ticket opens if $\ge 5\%$ of the budget is consumed over 6 hours.

### Simulate an Incident & Test Alerting

Run the following loop to flood the `/error` endpoint and trigger a burn rate spike:

```
while true; do curl -s http://localhost:8000/error > /dev/null; done

```

Observe the Prometheus alert dashboard (`http://localhost:9090/alerts`) transition from *Pending* to *Firing*, and check your configured chat channel for the live incident notification!

## 🔍 Exploring Dashboards in Grafana

1. Navigate to Grafana at `http://localhost:3000` (Login: `admin` / `admin`).

2. Add the following data sources:

   * **Prometheus:** `http://prometheus:9090`

   * **Loki:** `http://loki:3100` (OTLP native)

   * **Tempo:** `http://tempo:3200`

3. Use Grafana **Explore** to query traces, inspect logs with injected `trace_id` fields, and examine live burn rate metrics.

## 💡 Why This Project Matters for SRE Roles

* **Eliminates Support Guesswork:** Demonstrates how distributed trace correlation reduces Mean Time to Resolution (MTTR) from minutes to seconds.

* **Proactive Reliability Engineering:** Focuses on SLOs and user-centric error budgeting instead of chasing arbitrary server CPU/memory spikes.
