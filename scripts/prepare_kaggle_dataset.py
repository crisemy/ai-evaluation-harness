"""Download the Question-Answer Dataset from Kaggle and transform it to the harness schema."""

import json
import csv
import os
from datetime import datetime, timezone

import kagglehub

DATASET_ID = "veeralakrishna/questionanswer-dataset"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "qa_kaggle.json")


def transform_to_schema(source_path: str) -> dict:
    entries = []
    seen_ids: set[str] = set()

    with open(source_path, encoding="latin-1") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for idx, row in enumerate(reader):
            question = row.get("Question", "").strip()
            answer = row.get("Answer", "").strip()
            article = row.get("ArticleTitle", "").strip()
            difficulty = row.get("DifficultyFromAnswerer", "").strip().lower()

            if not question or not answer:
                continue

            entry_id = f"kaggle-{idx:04d}"
            if entry_id in seen_ids:
                continue
            seen_ids.add(entry_id)

            entry = {
                "id": entry_id,
                "input": question,
                "expected_output": answer,
                "category": article,
                "tags": ["kaggle", "wikipedia", article.replace(" ", "_").lower()],
                "metadata": {
                    "source": "kaggle",
                    "dataset": DATASET_ID,
                    "article": article,
                },
            }

            if difficulty in ("easy", "medium", "hard"):
                entry["difficulty"] = difficulty

            entries.append(entry)

    return {
        "format_version": "1.0",
        "dataset": {
            "name": "kaggle-qa-dataset",
            "description": "Manually-generated factoid question/answer pairs with difficulty ratings from Wikipedia articles",
            "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "entries": entries,
        },
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Downloading {DATASET_ID} from Kaggle...")
    cache_path = kagglehub.dataset_download(DATASET_ID)

    source_file = os.path.join(
        cache_path,
        "Question_Answer_Dataset_v1.2",
        "S10",
        "question_answer_pairs.txt",
    )

    print(f"Transforming {source_file}...")
    dataset = transform_to_schema(source_file)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    count = len(dataset["dataset"]["entries"])
    print(f"Written {count} entries to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
