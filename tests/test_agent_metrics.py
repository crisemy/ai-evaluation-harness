import pytest

from harness.metrics.agent import (
    GoalAchievement,
    StepCorrectness,
    ToolSelection,
    TrajectoryCoherence,
)


class TestStepCorrectness:
    def test_name(self):
        m = StepCorrectness()
        assert m.name == "step_correctness"

    def test_no_steps(self):
        m = StepCorrectness()
        result = m.evaluate("", "", {"trajectory_steps": []})
        assert not result.passed
        assert result.score == 0.0

    def test_no_expected_steps(self):
        m = StepCorrectness()
        steps = [{"step_index": 0, "tool_name": "search"}]
        result = m.evaluate("", "", {"trajectory_steps": steps})
        assert result.passed
        assert result.score == 1.0

    def test_all_steps_match(self):
        m = StepCorrectness()
        steps = [{"step_index": 0, "tool_name": "search"}]
        expected = [{"tool_name": "search"}]
        result = m.evaluate("", "", {"trajectory_steps": steps, "expected_trajectory": expected})
        assert result.passed
        assert result.score == 1.0

    def test_step_mismatch(self):
        m = StepCorrectness()
        steps = [{"step_index": 0, "tool_name": "search"}]
        expected = [{"tool_name": "compute"}]
        result = m.evaluate("", "", {"trajectory_steps": steps, "expected_trajectory": expected})
        assert not result.passed
        assert result.score == 0.0


class TestGoalAchievement:
    def test_name(self):
        m = GoalAchievement()
        assert m.name == "goal_achievement"

    def test_exact_match(self):
        m = GoalAchievement()
        result = m.evaluate("Full refund within 30 days", "Full refund within 30 days")
        assert result.passed
        assert result.score == 1.0

    def test_mismatch(self):
        m = GoalAchievement()
        result = m.evaluate("No refund", "Full refund within 30 days")
        assert not result.passed
        assert result.score == 0.0

    def test_no_response(self):
        m = GoalAchievement()
        result = m.evaluate("", "expected")
        assert not result.passed
        assert result.score == 0.0

    def test_no_expected(self):
        m = GoalAchievement()
        result = m.evaluate("some answer", "")
        assert result.passed
        assert result.score == 1.0


class TestToolSelection:
    def test_name(self):
        m = ToolSelection()
        assert m.name == "tool_selection"

    def test_no_expected_tools(self):
        m = ToolSelection()
        steps = [{"tool_name": "search"}, {"tool_name": "read"}]
        result = m.evaluate("", "", {"trajectory_steps": steps})
        assert result.passed

    def test_all_tools_correct(self):
        m = ToolSelection()
        steps = [{"tool_name": "search"}, {"tool_name": "compute"}]
        result = m.evaluate("", "", {"trajectory_steps": steps, "expected_tools": ["search", "compute"]})
        assert result.passed
        assert result.score == 1.0

    def test_extra_tool(self):
        m = ToolSelection()
        steps = [{"tool_name": "search"}, {"tool_name": "extra_tool"}]
        result = m.evaluate("", "", {"trajectory_steps": steps, "expected_tools": ["search"]})
        assert result.score < 1.0

    def test_missing_tool(self):
        m = ToolSelection()
        steps = [{"tool_name": "search"}]
        result = m.evaluate("", "", {"trajectory_steps": steps, "expected_tools": ["search", "compute"]})
        assert result.score < 1.0

    def test_no_tools_used(self):
        m = ToolSelection()
        result = m.evaluate("", "", {"trajectory_steps": [], "expected_tools": ["search"]})
        assert not result.passed
        assert result.score == 0.0


class TestTrajectoryCoherence:
    def test_name(self):
        m = TrajectoryCoherence()
        assert m.name == "trajectory_coherence"

    def test_no_steps(self):
        m = TrajectoryCoherence()
        result = m.evaluate("", "", {"trajectory_steps": []})
        assert not result.passed
        assert result.score == 0.0

    def test_good_trajectory(self):
        m = TrajectoryCoherence()
        steps = [
            {"step_index": 0, "thought": "I need to search", "tool_name": "search", "tool_output": "result"},
            {"step_index": 1, "thought": "Now I have the answer"},
        ]
        result = m.evaluate("final answer", "", {"trajectory_steps": steps})
        assert result.passed
        assert result.score >= 0.5

    def test_no_thoughts(self):
        m = TrajectoryCoherence()
        steps = [
            {"step_index": 0, "tool_name": "search"},
        ]
        result = m.evaluate("", "", {"trajectory_steps": steps})
        assert result.score < 0.5
