"""Base connector interface for platform adapters."""

from abc import ABC, abstractmethod

from feedback_intelligence.schemas import ImportResult, ImportRow


class BaseConnector(ABC):
    """Abstract base for all platform connectors."""

    @abstractmethod
    def fetch(self) -> list[ImportRow]:
        """Fetch data from the platform. Returns list of ImportRow."""
        ...

    def validate(self, row: ImportRow) -> bool:
        """Validate a single row. Override for platform-specific logic."""
        return True

    def import_data(self, db_session) -> ImportResult:
        """Fetch, validate, and import data."""
        from feedback_intelligence.services.import_service import import_rows

        rows = self.fetch()
        valid_rows = [r for r in rows if self.validate(r)]
        return import_rows(db_session, valid_rows)
