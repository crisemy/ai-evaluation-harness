from harness.interfaces.dataset_loader import DatasetLoader
from harness.interfaces.metric import Metric
from harness.interfaces.observer import Observer
from harness.interfaces.provider import LLMProvider
from harness.interfaces.reporter import Reporter


class TestInterfacesAreAbstract:
    def test_dataset_loader_is_abstract(self):
        assert DatasetLoader.__name__ == "DatasetLoader"

    def test_provider_is_abstract(self):
        assert LLMProvider.__name__ == "LLMProvider"

    def test_metric_is_abstract(self):
        assert Metric.__name__ == "Metric"

    def test_reporter_is_abstract(self):
        assert Reporter.__name__ == "Reporter"

    def test_observer_is_abstract(self):
        assert Observer.__name__ == "Observer"
