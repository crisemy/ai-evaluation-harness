import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from harness.contracts.trace import ObservableEvent
from harness.observers import TraceObserver


class TestTraceObserver:
    def test_emit_no_context(self):
        obs = TraceObserver()
        obs.emit(ObservableEvent(event_type="test", component="test", timestamp=datetime.now(timezone.utc), data={}))
        assert len(obs.get_all_traces()) == 0

    def test_emit_with_context(self):
        obs = TraceObserver()
        obs.set_context("trace-1", "eval-1")
        obs.emit(ObservableEvent(event_type="start", component="cli", timestamp=datetime.now(timezone.utc), data={"msg": "hello"}))
        traces = obs.get_all_traces()
        assert len(traces) == 1
        assert traces[0].trace_id == "trace-1"
        assert traces[0].evaluation_id == "eval-1"
        assert len(traces[0].events) == 1
        assert traces[0].events[0].event_type == "start"

    def test_emit_multiple_events(self):
        obs = TraceObserver()
        obs.set_context("t1", "e1")
        now = datetime.now(timezone.utc)
        obs.emit(ObservableEvent(event_type="a", component="c", timestamp=now, data={}))
        obs.emit(ObservableEvent(event_type="b", component="c", timestamp=now, data={}))
        traces = obs.get_all_traces()
        assert len(traces[0].events) == 2

    def test_get_trace_by_evaluation_id(self):
        obs = TraceObserver()
        obs.set_context("t1", "eval-1")
        obs.emit(ObservableEvent(event_type="x", component="c", timestamp=datetime.now(timezone.utc), data={}))
        obs.clear_context()
        obs.set_context("t2", "eval-2")
        obs.emit(ObservableEvent(event_type="y", component="c", timestamp=datetime.now(timezone.utc), data={}))

        trace = obs.get_trace("eval-1")
        assert trace is not None
        assert trace.trace_id == "t1"
        assert len(trace.events) == 1

        assert obs.get_trace("nonexistent") is None

    def test_clear_context_drops_events(self):
        obs = TraceObserver()
        obs.set_context("t1", "e1")
        obs.emit(ObservableEvent(event_type="a", component="c", timestamp=datetime.now(timezone.utc), data={}))
        obs.clear_context()
        obs.emit(ObservableEvent(event_type="b", component="c", timestamp=datetime.now(timezone.utc), data={}))
        traces = obs.get_all_traces()
        assert len(traces) == 1
        assert len(traces[0].events) == 1

    def test_flush_writes_ndjson(self):
        obs = TraceObserver()
        obs.set_context("t1", "e1")
        obs.emit(ObservableEvent(event_type="test", component="c", timestamp=datetime.now(timezone.utc), data={"k": "v"}))
        obs.clear_context()
        obs.set_context("t2", "e2")
        obs.emit(ObservableEvent(event_type="test2", component="c", timestamp=datetime.now(timezone.utc), data={}))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ndjson", delete=False) as f:
            out_path = f.name

        try:
            result = obs.flush(out_path)
            assert result == out_path

            content = Path(out_path).read_text(encoding="utf-8")
            lines = [l for l in content.strip().splitlines() if l.strip()]
            assert len(lines) == 2
            for line in lines:
                parsed = json.loads(line)
                assert "trace_id" in parsed
                assert "evaluation_id" in parsed
                assert "events" in parsed
        finally:
            Path(out_path).unlink(missing_ok=True)

    def test_flush_no_path(self):
        obs = TraceObserver()
        obs.set_context("t1", "e1")
        obs.emit(ObservableEvent(event_type="t", component="c", timestamp=datetime.now(timezone.utc), data={}))
        assert obs.flush(path=None) is None

    def test_load_ndjson(self):
        data = [
            {"trace_id": "t1", "evaluation_id": "e1", "events": [
                {"event_type": "start", "component": "cli", "timestamp": "2025-01-01T00:00:00+00:00", "data": {}, "duration_ms": None},
            ]},
            {"trace_id": "t2", "evaluation_id": "e2", "events": []},
        ]
        content = "\n".join(json.dumps(d) for d in data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ndjson", delete=False) as f:
            f.write(content)
            in_path = f.name

        try:
            traces = TraceObserver.load_ndjson(in_path)
            assert len(traces) == 2
            assert traces[0].trace_id == "t1"
            assert traces[1].evaluation_id == "e2"
            assert len(traces[0].events) == 1
            assert traces[0].events[0].event_type == "start"
        finally:
            Path(in_path).unlink(missing_ok=True)

    def test_load_ndjson_nonexistent(self):
        traces = TraceObserver.load_ndjson("nonexistent_file.ndjson")
        assert traces == []
