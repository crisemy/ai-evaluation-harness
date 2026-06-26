from unittest.mock import create_autospec

import pytest

from harness.contracts.agent import AgentStep, AgentTrajectory
from harness.evaluator_agent import AgentEvaluator, AgentSample
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
def agent_metrics():
    return [_mock_metric("step_correctness"), _mock_metric("goal_achievement")]


@pytest.fixture
def agent_samples():
    return [
        AgentSample(
            task="What is the refund policy?",
            expected_output="Full refund within 30 days",
            trajectory=AgentTrajectory(
                entry_id="entry-001",
                task="What is the refund policy?",
                steps=[
                    AgentStep(step_index=0, thought="I need to look up the refund policy", tool_name="search_docs", tool_input={"query": "refund policy"}, tool_output="30 day refund policy"),
                    AgentStep(step_index=1, thought="The policy says 30 day refund", tool_name=None, tool_input=None, tool_output=None),
                ],
                final_answer="Full refund within 30 days",
                total_duration_ms=1500,
                total_tokens=250,
            ),
        ),
    ]


class TestAgentEvaluator:
    def test_evaluate_returns_summary(self, agent_metrics, agent_samples):
        evaluator = AgentEvaluator(agent_metrics)
        summary = evaluator.evaluate(agent_samples)
        assert summary.evaluation_id
        assert summary.summary.total_entries == 1

    def test_evaluate_multiple_samples(self, agent_metrics):
        evaluator = AgentEvaluator(agent_metrics)
        samples = [
            AgentSample(
                task="Q1", expected_output="A1",
                trajectory=AgentTrajectory(entry_id="e1", task="Q1", steps=[], final_answer="A1"),
            ),
            AgentSample(
                task="Q2", expected_output="A2",
                trajectory=AgentTrajectory(entry_id="e2", task="Q2", steps=[], final_answer="A2"),
            ),
        ]
        summary = evaluator.evaluate(samples)
        assert summary.summary.total_entries == 2
        assert summary.summary.passed == 2

    def test_evaluate_no_samples(self, agent_metrics):
        evaluator = AgentEvaluator(agent_metrics)
        with pytest.raises(HarnessError, match="No agent samples"):
            evaluator.evaluate([])

    def test_evaluate_no_metrics(self):
        with pytest.raises(HarnessError, match="At least one agent metric"):
            AgentEvaluator(metrics=[])

    def test_evaluate_no_final_answer(self, agent_metrics):
        evaluator = AgentEvaluator(agent_metrics)
        samples = [
            AgentSample(
                task="Q", expected_output="A",
                trajectory=AgentTrajectory(entry_id="e1", task="Q", steps=[], final_answer=None),
            ),
        ]
        summary = evaluator.evaluate(samples)
        assert summary.summary.total_entries == 1

    def test_metric_names(self, agent_metrics):
        evaluator = AgentEvaluator(agent_metrics)
        assert evaluator.metric_names == ["step_correctness", "goal_achievement"]

    def test_evaluate_with_expected_trajectory(self, agent_metrics):
        evaluator = AgentEvaluator(agent_metrics)
        samples = [
            AgentSample(
                task="Q", expected_output="A",
                trajectory=AgentTrajectory(
                    entry_id="e1", task="Q",
                    steps=[AgentStep(step_index=0, tool_name="search")],
                    final_answer="A",
                ),
                expected_trajectory=[{"tool_name": "search"}],
                expected_tools=["search"],
            ),
        ]
        summary = evaluator.evaluate(samples)
        assert summary.summary.total_entries == 1
