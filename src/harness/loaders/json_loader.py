from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from harness.contracts.dataset import Dataset, DatasetEntry, DatasetMetadata, Difficulty
from harness.errors import FormatError, LoadError, ValidationError
from harness.interfaces.dataset_loader import DatasetLoader

SUPPORTED_VERSIONS = {"1.0", "1.1"}


class JSONDatasetLoader(DatasetLoader):
    def load(self, path: str, format: str = "json") -> Dataset:
        path_obj = Path(path)

        if format != "json":
            raise FormatError(format)

        try:
            with path_obj.open(encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError:
            raise LoadError(str(path_obj), "File not found")
        except json.JSONDecodeError as e:
            raise LoadError(str(path_obj), f"Invalid JSON: {e}")

        return self._parse(raw, path_obj)

    def _parse(self, raw: dict, path_obj: Path) -> Dataset:
        fmt_ver = raw.get("format_version", "")
        if fmt_ver not in SUPPORTED_VERSIONS:
            raise FormatError(
                fmt_ver,
                f"Unsupported format version '{fmt_ver}'. Supported: {SUPPORTED_VERSIONS}",
            )

        ds_raw = raw.get("dataset")
        if not ds_raw:
            raise LoadError(str(path_obj), "Missing 'dataset' key in root")

        entries_raw = ds_raw.get("entries", [])
        if not entries_raw:
            raise LoadError(str(path_obj), "Dataset contains no entries")

        created = ds_raw.get("created")
        created_dt = None
        if created:
            try:
                created_dt = datetime.fromisoformat(created)
            except ValueError:
                pass

        metadata = DatasetMetadata(
            name=ds_raw.get("name", path_obj.stem),
            description=ds_raw.get("description"),
            created=created_dt,
            format_version=fmt_ver,
        )

        entries = [self._parse_entry(e, i) for i, e in enumerate(entries_raw)]
        return Dataset(metadata=metadata, entries=entries)

    def _parse_entry(self, raw: dict, index: int) -> DatasetEntry:
        entry_id = raw.get("id", f"entry-{index:04d}")
        input_text = raw.get("input", "")
        expected = raw.get("expected_output", "")

        errors = []
        if not input_text:
            errors.append("input")
        if not expected:
            errors.append("expected_output")
        if errors:
            fields = ", ".join(errors)
            raise ValidationError(
                fields, f"Entry {entry_id} missing required fields: {fields}"
            )

        difficulty_raw = raw.get("difficulty")
        difficulty = None
        if difficulty_raw:
            try:
                difficulty = Difficulty(difficulty_raw.lower())
            except ValueError:
                pass

        metadata = raw.get("metadata") or {}
        context_docs = raw.get("context_documents")
        if context_docs is not None:
            metadata["context_documents"] = context_docs

        return DatasetEntry(
            id=entry_id,
            input=input_text,
            expected_output=expected,
            category=raw.get("category"),
            difficulty=difficulty,
            tags=raw.get("tags"),
            metadata=metadata or None,
        )

    def validate(self, entry: dict) -> None:
        if not entry.get("input"):
            raise ValidationError("input", "Missing required field: input")
        if not entry.get("expected_output"):
            raise ValidationError(
                "expected_output", "Missing required field: expected_output"
            )
