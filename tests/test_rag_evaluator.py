from datetime import datetime, timezone
from unittest.mock import MagicMock, create_autospec

import pytest

from harness.contracts.rag import Document
from harness.evaluator_rag import RAGEvaluator, RAGSample
from harness.errors import HarnessError
from harness.interfaces.metric import Metric


def _mock_metric(name: str, score: float = 1.0, passed: bool = True):
    m = create_autospec(Metric)
    m.name = name
    m.threshold = 0.5

    def evaluate(response, expected, context=None):
        from harness.contracts.evaluation import MetricResult
        return MetricResult(
            metric_name=name,
            score=score,
            passed=passed,
            explanation=f"{name} result",
            threshold=0.5,
        )

    m.evaluate.side_effect = evaluate
    return m


@pytest.fixture
def rag_metrics():
    return [_mock_metric("faithfulness"), _mock_metric("answer_relevancy")]


@pytest.fixture
def rag_samples():
    return [
        RAGSample(
            query="What is the refund policy?",
            expected_output="Full refund within 30 days",
            context_documents=[
                Document(id="d1", text="Customers may request a full refund within 30 days."),
            ],
            response="You can get a full refund within 30 days.",
        ),
    ]


class TestRAGEvaluator:
    def test_evaluate_returns_summary(self, rag_metrics, rag_samples):
        evaluator = RAGEvaluator(rag_metrics)
        summary = evaluator.evaluate(rag_samples)
        assert summary.evaluation_id
        assert summary.summary.total_entries == 1

    def test_evaluate_multiple_samples(self, rag_metrics):
        evaluator = RAGEvaluator(rag_metrics)
        samples = [
            RAGSample(query="Q1", expected_output="A1", context_documents=[Document(id="d1", text="ctx1")], response="A1"),
            RAGSample(query="Q2", expected_output="A2", context_documents=[Document(id="d2", text="ctx2")], response="A2"),
        ]
        summary = evaluator.evaluate(samples)
        assert summary.summary.total_entries == 2
        assert summary.summary.passed == 2

    def test_evaluate_no_samples(self, rag_metrics):
        evaluator = RAGEvaluator(rag_metrics)
        with pytest.raises(HarnessError, match="No RAG samples"):
            evaluator.evaluate([])

    def test_evaluate_no_metrics(self):
        with pytest.raises(HarnessError, match="At least one RAG metric"):
            RAGEvaluator(metrics=[])

    def test_evaluate_no_response_graceful(self, rag_metrics):
        evaluator = RAGEvaluator(rag_metrics)
        samples = [
            RAGSample(
                query="Q",
                expected_output="A",
                context_documents=[Document(id="d1", text="ctx")],
                response=None,
            ),
        ]
        summary = evaluator.evaluate(samples)
        assert summary.summary.total_entries == 1
        assert summary.summary.failed == 1

    def test_metric_names(self, rag_metrics):
        evaluator = RAGEvaluator(rag_metrics)
        assert evaluator.metric_names == ["faithfulness", "answer_relevancy"]

    def test_evaluate_with_context_provider(self, rag_metrics, rag_samples):
        ctx_provider = MagicMock()
        ctx_provider.get_context.return_value = [Document(id="d1", text="some context")]
        evaluator = RAGEvaluator(rag_metrics, context_provider=ctx_provider)
        summary = evaluator.evaluate(rag_samples)
        assert summary.summary.total_entries == 1
