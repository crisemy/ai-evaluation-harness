class HarnessError(Exception):
    pass


class ValidationError(HarnessError):
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"{field}: {message}")


class FormatError(HarnessError):
    def __init__(self, format: str, message: str = "Unsupported format"):
        self.format = format
        super().__init__(f"{format}: {message}")


class LoadError(HarnessError):
    def __init__(self, path: str, message: str = "Failed to load"):
        self.path = path
        super().__init__(f"{path}: {message}")


class MetricError(HarnessError):
    pass
