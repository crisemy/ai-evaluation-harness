from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import create_autospec

import pytest

from harness.contracts.dataset import Dataset, DatasetEntry, DatasetMetadata
from harness.contracts.execution import ExecutionResponse, TokenUsage
from harness.errors import HarnessError
from harness.executor import ExecutorConfig, PromptExecutor
from harness.interfaces.dataset_loader import DatasetLoader
from harness.interfaces.provider import LLMProvider

FIXTURES = Path(__file__).parent / "fixtures"


def _mock_response(entry_id: str, text: str = "mock answer") -> ExecutionResponse:
    return ExecutionResponse(
        entry_id=entry_id,
        text=text,
        provider="ollama",
        model="phi3",
        latency_ms=100,
        token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_loader():
    loader = create_autospec(DatasetLoader)
    loader.load.return_value = Dataset(
        metadata=DatasetMetadata(name="test", format_version="1.0"),
        entries=[
            DatasetEntry(id="e1", input="Q1?", expected_output="A1"),
            DatasetEntry(id="e2", input="Q2?", expected_output="A2"),
        ],
    )
    return loader


@pytest.fixture
def mock_provider():
    provider = create_autospec(LLMProvider)
    provider.provider_name = "ollama"

    def generate(req):
        return _mock_response(req.entry_id)

    provider.generate.side_effect = generate
    return provider


@pytest.fixture
def executor(mock_loader, mock_provider):
    return PromptExecutor(mock_loader, mock_provider)


class TestPromptExecutor:
    def test_execute_dataset(self, executor):
        responses = executor.execute_dataset(
            Dataset(
                metadata=DatasetMetadata(name="t", format_version="1.0"),
                entries=[DatasetEntry(id="e1", input="Q?", expected_output="A")],
            )
        )
        assert len(responses) == 1
        assert responses[0].entry_id == "e1"
        assert responses[0].provider == "ollama"

    def test_execute_from_path(self, mock_loader, mock_provider):
        dataset_path = str(FIXTURES / "sample_dataset.json")
        executor = PromptExecutor(mock_loader, mock_provider)
        responses = executor.execute(dataset_path)
        assert len(responses) == 2
        assert responses[0].entry_id == "e1"
        assert responses[1].entry_id == "e2"

    def test_execute_entry_single(self, executor):
        entry = DatasetEntry(id="e1", input="Hello?", expected_output="Hi")
        response = executor.execute_entry(entry)
        assert response.text == "mock answer"

    def test_execute_entry_passes_config(self, mock_loader, mock_provider):
        config = ExecutorConfig(
            provider="ollama",
            model="gemma4",
            temperature=0.1,
            max_tokens=512,
        )
        executor = PromptExecutor(mock_loader, mock_provider, config)
        entry = DatasetEntry(id="e1", input="Test?", expected_output="Test")
        executor.execute_entry(entry)

        call_request = mock_provider.generate.call_args[0][0]
        assert call_request.model == "gemma4"
        assert call_request.temperature == 0.1
        assert call_request.max_tokens == 512

    def test_provider_error_propagates(self, executor):
        executor._provider.generate.side_effect = HarnessError("API down")
        entry = DatasetEntry(id="e1", input="Q?", expected_output="A")
        with pytest.raises(HarnessError):
            executor.execute_entry(entry)

    def test_execute_entry_tracks_tokens(self, mock_loader, mock_provider):
        executor = PromptExecutor(mock_loader, mock_provider)
        entry = DatasetEntry(id="e1", input="Q?", expected_output="A")
        response = executor.execute_entry(entry)
        assert response.token_usage.prompt_tokens == 10
        assert response.token_usage.completion_tokens == 5
        assert response.token_usage.total_tokens == 15
