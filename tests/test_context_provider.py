from harness.contracts.rag import Document
from harness.providers.context import DatasetContextProvider


class TestDatasetContextProvider:
    def test_returns_all_documents(self):
        docs = [
            Document(id="d1", text="doc1"),
            Document(id="d2", text="doc2"),
        ]
        provider = DatasetContextProvider(docs)
        result = provider.get_context("query")
        assert len(result) == 2
        assert result[0].id == "d1"
        assert result[1].id == "d2"

    def test_respects_top_k(self):
        docs = [
            Document(id="d1", text="doc1"),
            Document(id="d2", text="doc2"),
            Document(id="d3", text="doc3"),
        ]
        provider = DatasetContextProvider(docs)
        result = provider.get_context("query", top_k=2)
        assert len(result) == 2

    def test_empty_documents(self):
        provider = DatasetContextProvider([])
        result = provider.get_context("query")
        assert result == []
