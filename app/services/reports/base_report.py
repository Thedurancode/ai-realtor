"""Abstract base class for PDF reports."""
from abc import ABC, abstractmethod
from io import BytesIO


class BaseReport(ABC):
    """Base class that all PDF report types must implement."""

    @property
    @abstractmethod
    def report_type(self) -> str:
        """Unique identifier, e.g. 'property_overview'."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name, e.g. 'Property Overview'."""

    @abstractmethod
    def generate(self, context: dict) -> BytesIO:
        """Generate the PDF and return it as an in-memory buffer."""

    def get_filename(self, context: dict) -> str:
        """Return a safe filename for the PDF attachment."""
        address = context.get("property", {}).get("address", "property")
        safe = address.replace(",", "").replace(" ", "_").replace("/", "-")[:60]
        return f"{self.report_type}_{safe}.pdf"
