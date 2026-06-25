import json
from pathlib import Path

import pytest

from harness.contracts.dataset import Difficulty
from harness.errors import FormatError, LoadError, ValidationError
from harness.loaders.json_loader import JSONDatasetLoader

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def loader():
    return JSONDatasetLoader()


@pytest.fixture
def sample_path():
    return FIXTURES / "sample_dataset.json"


class TestJSONDatasetLoader:
    def test_load_valid_json(self, loader, sample_path):
        dataset = loader.load(str(sample_path))
        assert dataset.metadata.name == "sample-qa"
        assert len(dataset.entries) == 3

    def test_entry_fields(self, loader, sample_path):
        dataset = loader.load(str(sample_path))
        entry = dataset.entries[0]
        assert entry.id == "qa-001"
        assert entry.input == "What is the capital of France?"
        assert entry.expected_output == "Paris"
        assert entry.category == "geography"
        assert entry.difficulty == Difficulty.EASY
        assert entry.tags == ["capital", "europe"]

    def test_load_nonexistent_file(self, loader):
        with pytest.raises(LoadError, match="File not found"):
            loader.load("nonexistent.json")

    def test_load_invalid_json(self, loader, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{invalid")
        with pytest.raises(LoadError, match="Invalid JSON"):
            loader.load(str(bad))

    def test_load_unsupported_format_version(self, tmp_path, loader):
        p = tmp_path / "bad_ver.json"
        p.write_text(
            json.dumps(
                {
                    "format_version": "99.0",
                    "dataset": {"name": "x", "entries": []},
                }
            )
        )
        with pytest.raises(FormatError, match="99.0"):
            loader.load(str(p))

    def test_load_no_entries(self, tmp_path, loader):
        p = tmp_path / "empty.json"
        p.write_text(
            json.dumps(
                {
                    "format_version": "1.0",
                    "dataset": {"name": "empty", "entries": []},
                }
            )
        )
        with pytest.raises(LoadError, match="no entries"):
            loader.load(str(p))

    def test_load_missing_required_field(self, tmp_path, loader):
        p = tmp_path / "bad_entry.json"
        p.write_text(
            json.dumps(
                {
                    "format_version": "1.0",
                    "dataset": {
                        "name": "bad",
                        "entries": [{"id": "e1", "input": "", "expected_output": ""}],
                    },
                }
            )
        )
        with pytest.raises(ValidationError) as exc:
            loader.load(str(p))
        assert "input" in str(exc.value) or "expected_output" in str(exc.value)


class TestLoadKaggleDataset:
    def test_load_kaggle_dataset(self, loader):
        kaggle_path = Path(__file__).parent.parent / "datasets" / "qa_kaggle.json"
        if not kaggle_path.exists():
            pytest.skip("Kaggle dataset not found — run scripts/prepare_kaggle_dataset.py")
        dataset = loader.load(str(kaggle_path))
        assert len(dataset.entries) > 1000
        assert dataset.metadata.name == "kaggle-qa-dataset"

    def test_kaggle_entries_have_all_required_fields(self, loader):
        kaggle_path = Path(__file__).parent.parent / "datasets" / "qa_kaggle.json"
        if not kaggle_path.exists():
            pytest.skip("Kaggle dataset not found")
        dataset = loader.load(str(kaggle_path))
        for e in dataset.entries:
            assert e.id
            assert e.input
            assert e.expected_output
