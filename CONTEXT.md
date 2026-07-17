# Context

The rapid adoption of LLMs, Retrieval-Augmented Generation (RAG), AI Agents, and AI Assistants has created a new challenge for engineering teams.

Traditional software testing approaches rely on deterministic outputs and exact assertions. AI systems are probabilistic and may generate multiple acceptable responses for the same input.

As a result, organizations often lack reliable mechanisms to:

* Detect quality regressions.
* Measure answer correctness.
* Evaluate hallucinations.
* Assess faithfulness to source material.
* Compare model versions.
* Monitor prompt changes.
* Validate agent behavior.

AI Evaluation Harness exists to address these challenges by providing a structured and repeatable evaluation framework for AI-powered systems, governed by the AI QA Core Framework methodology for risk-aware quality management and automated via CI/CD pipelines and interactive dashboards.

The project is designed for QA Engineers, AI Engineers, Reliability Engineers, Software Engineers, and engineering teams building AI-driven products.

## Dataset Pipeline

The project uses real-world datasets sourced from Kaggle for evaluation credibility. The current dataset is the [Question-Answer Dataset](https://www.kaggle.com/datasets/veeralakrishna/questionanswer-dataset) with 1,456 entries spanning multiple Wikipedia articles. A transformation script (`scripts/prepare_kaggle_dataset.py`) downloads and converts raw data into the project's standardized JSON schema.
