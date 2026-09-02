class ProviderError(Exception):
    """Base class for provider-layer failures."""


class DatasetUnavailableError(FileNotFoundError, ProviderError):
    """A configured dataset cannot be read or is unavailable."""


class ProviderUnavailableError(RuntimeError, ProviderError):
    """A provider dependency is unavailable."""


class InvalidProviderQueryError(ValueError, ProviderError):
    """A provider query is invalid."""


class UnsupportedProviderOperationError(ValueError, ProviderError):
    """A provider cannot perform the requested operation."""


class DataUnavailableError(LookupError, ProviderError):
    """A valid query has no data in the provider coverage or range."""