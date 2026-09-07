"""Custom exceptions for Revision Forge.

Every subsystem raises its own exception type so callers can catch exactly
what they care about, and every error carries a clear message for the logs.
"""


class RevisionForgeError(Exception):
    """Base class for all Revision Forge errors."""


class ConfigurationError(RevisionForgeError):
    """Configuration files are missing, invalid, or incomplete."""


class AnkiConnectionError(RevisionForgeError):
    """Anki is not running, AnkiConnect is unreachable, or it returned an error."""


class ResourceProcessingError(RevisionForgeError):
    """A resource (e.g. a PDF) could not be loaded or processed."""


class ValidationError(RevisionForgeError):
    """Data (e.g. an LLM-generated card) failed schema validation."""


class ResearchError(RevisionForgeError):
    """Web research or syllabus retrieval failed."""


class ApprovalRequiredError(RevisionForgeError):
    """An Anki write was attempted without user approval."""


class DatabaseError(RevisionForgeError):
    """A database operation failed."""
