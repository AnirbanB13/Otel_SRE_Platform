import time
import logging
from fastapi import FastAPI, Response

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Shared resource so all signals carry the same service name
resource = Resource.create({"service.name": "sre-demo-service"})

# ── Traces ────────────────────────────────────────────────────────────────────
trace_provider = TracerProvider(resource=resource)
trace_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True))
)
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer("sre-demo-service")

# ── Metrics ───────────────────────────────────────────────────────────────────
metric_exporter = OTLPMetricExporter(endpoint="http://localhost:4317", insecure=True)
metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter("sre-demo-service")

# Custom metrics
request_counter = meter.create_counter(
    name="app_requests_total",
    description="Total number of requests",
    unit="1",
)
error_counter = meter.create_counter(
    name="app_errors_total",
    description="Total number of errors",
    unit="1",
)
request_duration = meter.create_histogram(
    name="app_request_duration_seconds",
    description="Request duration in seconds",
    unit="s",
)

# ── Logging ───────────────────────────────────────────────────────────────────
# Instrument logging BEFORE basicConfig so OTel injects trace context
LoggingInstrumentor().instrument(set_logging_format=False)

# Filter to ensure otelTraceID/otelSpanID always exist (fallback outside spans)
class TraceContextFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "otelTraceID"):
            record.otelTraceID = "0" * 32
        if not hasattr(record, "otelSpanID"):
            record.otelSpanID = "0" * 16
        return True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] %(message)s"
)
for handler in logging.root.handlers:
    handler.addFilter(TraceContextFilter())

logger = logging.getLogger("app")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI()
FastAPIInstrumentor.instrument_app(app)


@app.get("/")
def read_root():
    start = time.time()
    with tracer.start_as_current_span("business_logic_processing") as span:
        span.set_attribute("user.tier", "enterprise")
        logger.info("Processing root request successfully.")
        time.sleep(0.05)  # Simulate database work

    request_counter.add(1, {"endpoint": "/", "status": "200"})
    request_duration.record(time.time() - start, {"endpoint": "/"})
    return {"status": "success", "message": "Observed via OpenTelemetry!"}


@app.get("/error")
def trigger_error(response: Response):
    start = time.time()
    with tracer.start_as_current_span("failing_payment_gateway") as span:
        span.set_attribute("error.type", "PaymentTimeout")
        span.record_exception(Exception("Gateway timeout"))
        logger.error("Payment gateway failed to respond within threshold!")
        response.status_code = 500

    request_counter.add(1, {"endpoint": "/error", "status": "500"})
    error_counter.add(1, {"endpoint": "/error", "error_type": "PaymentTimeout"})
    request_duration.record(time.time() - start, {"endpoint": "/error"})
    return {"status": "error", "message": "Simulated Gateway Failure"}
