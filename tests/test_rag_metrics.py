from unittest.mock import MagicMock, patch

import pytest

from harness.errors import MetricError
from harness.metrics.rag import AnswerRelevancy, ContextPrecision, ContextRecall, Faithfulness


class TestFaithfulness:
    def test_name(self):
        m = Faithfulness()
        assert m.name == "faithfulness"

    @patch("harness.metrics.rag.faithfulness.HAS_DEEPEVAL", False)
    def test_requires_deepeval(self):
        m = Faithfulness()
        with pytest.raises(MetricError, match="deepeval is not installed"):
            m.evaluate("response", "expected", {"context_documents": ["doc"]})

    def test_no_context_docs(self):
        m = Faithfulness()
        result = m.evaluate("response", "expected", {})
        assert not result.passed
        assert result.score == 0.0

    @patch("harness.metrics.rag.faithfulness._FaithfulnessMetric")
    def test_evaluate_with_mock(self, mock_metric_cls):
        mock_instance = MagicMock()
        mock_instance.measure.return_value = MagicMock(score=0.85, reason="Faithful")
        mock_instance.score = 0.85
        mock_metric_cls.return_value = mock_instance

        m = Faithfulness()
        result = m.evaluate("response", "expected", {"context_documents": ["doc1"]})
        assert result.score == 0.85
        assert result.passed
        assert result.metric_name == "faithfulness"


class TestAnswerRelevancy:
    def test_name(self):
        m = AnswerRelevancy()
        assert m.name == "answer_relevancy"

    @patch("harness.metrics.rag.answer_relevancy.HAS_DEEPEVAL", False)
    def test_requires_deepeval(self):
        m = AnswerRelevancy()
        with pytest.raises(MetricError, match="deepeval is not installed"):
            m.evaluate("response", "expected")

    @patch("harness.metrics.rag.answer_relevancy._AnswerRelevancyMetric")
    def test_evaluate_with_mock(self, mock_metric_cls):
        mock_instance = MagicMock()
        mock_instance.measure.return_value = MagicMock(score=0.9, reason="Relevant")
        mock_instance.score = 0.9
        mock_metric_cls.return_value = mock_instance

        m = AnswerRelevancy()
        result = m.evaluate("response", "expected", {"query": "What is X?"})
        assert result.score == 0.9
        assert result.passed


class TestContextPrecision:
    def test_name(self):
        m = ContextPrecision()
        assert m.name == "context_precision"

    @patch("harness.metrics.rag.context_precision.HAS_DEEPEVAL", False)
    def test_requires_deepeval(self):
        m = ContextPrecision()
        with pytest.raises(MetricError, match="deepeval is not installed"):
            m.evaluate("response", "expected", {"context_documents": ["doc"]})

    def test_no_context_docs(self):
        m = ContextPrecision()
        result = m.evaluate("response", "expected", {})
        assert not result.passed
        assert result.score == 0.0

    @patch("harness.metrics.rag.context_precision._ContextualPrecisionMetric")
    def test_evaluate_with_mock(self, mock_metric_cls):
        mock_instance = MagicMock()
        mock_instance.measure.return_value = MagicMock(score=0.75, reason="Precise")
        mock_instance.score = 0.75
        mock_metric_cls.return_value = mock_instance

        m = ContextPrecision()
        result = m.evaluate("response", "expected", {"context_documents": ["doc1", "doc2"]})
        assert result.score == 0.75
        assert result.passed


class TestContextRecall:
    def test_name(self):
        m = ContextRecall()
        assert m.name == "context_recall"

    @patch("harness.metrics.rag.context_recall.HAS_DEEPEVAL", False)
    def test_requires_deepeval(self):
        m = ContextRecall()
        with pytest.raises(MetricError, match="deepeval is not installed"):
            m.evaluate("response", "expected", {"context_documents": ["doc"]})

    def test_no_context_docs(self):
        m = ContextRecall()
        result = m.evaluate("response", "expected", {})
        assert not result.passed
        assert result.score == 0.0

    @patch("harness.metrics.rag.context_recall._ContextualRecallMetric")
    def test_evaluate_with_mock(self, mock_metric_cls):
        mock_instance = MagicMock()
        mock_instance.measure.return_value = MagicMock(score=0.8, reason="Good recall")
        mock_instance.score = 0.8
        mock_metric_cls.return_value = mock_instance

        m = ContextRecall()
        result = m.evaluate("response", "expected", {"context_documents": ["doc1"]})
        assert result.score == 0.8
        assert result.passed
