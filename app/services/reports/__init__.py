"""Report registry — register_report() / get_report() / list_report_types()."""
from .base_report import BaseReport

_registry: dict[str, BaseReport] = {}


def register_report(report: BaseReport):
    _registry[report.report_type] = report


def get_report(report_type: str) -> BaseReport:
    report = _registry.get(report_type)
    if not report:
        available = ", ".join(_registry.keys()) or "(none)"
        raise ValueError(f"Unknown report type '{report_type}'. Available: {available}")
    return report


def list_report_types() -> list[dict]:
    return [
        {"type": r.report_type, "name": r.display_name}
        for r in _registry.values()
    ]


# Auto-register bundled reports on import
from . import property_overview_report  # noqa: F401, E402
