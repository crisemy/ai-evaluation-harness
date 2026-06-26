import pytest

from harness.metrics.contains import Contains
from harness.metrics.exact_match import ExactMatch


class TestExactMatch:
    def test_exact_match_passes(self):
        m = ExactMatch()
        result = m.evaluate("Paris", "Paris")
        assert result.passed
        assert result.score == 1.0
        assert result.metric_name == "exact_match"

    def test_exact_match_fails(self):
        m = ExactMatch()
        result = m.evaluate("Paris", "London")
        assert not result.passed
        assert result.score == 0.0

    def test_exact_match_whitespace_mismatch(self):
        m = ExactMatch()
        result = m.evaluate("Paris ", "Paris")
        assert result.score == 1.0

    def test_exact_match_case_sensitive(self):
        m = ExactMatch()
        result = m.evaluate("paris", "Paris")
        assert not result.passed


class TestContains:
    def test_contains_found(self):
        m = Contains()
        result = m.evaluate("The capital is Paris indeed", "Paris")
        assert result.passed
        assert result.score == 1.0

    def test_contains_not_found(self):
        m = Contains()
        result = m.evaluate("The capital is London", "Paris")
        assert not result.passed
        assert result.score == 0.0

    def test_contains_case_insensitive_by_default(self):
        m = Contains()
        result = m.evaluate("The capital is PARIS", "paris")
        assert result.passed

    def test_contains_case_sensitive(self):
        m = Contains(case_sensitive=True)
        result = m.evaluate("The capital is PARIS", "paris")
        assert not result.passed

    def test_contains_passes_with_zero_threshold(self):
        m = Contains(threshold=0.0)
        result = m.evaluate("anything", "Paris")
        assert result.passed
        assert result.threshold == 0.0
