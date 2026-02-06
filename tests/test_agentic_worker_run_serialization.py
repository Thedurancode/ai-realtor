from datetime import date, datetime, timezone

from app.services.agentic.pipeline import AgenticResearchService, WorkerExecution


class _FakeDb:
    def __init__(self):
        self.rows = []
        self.commits = 0

    def add(self, row):
        self.rows.append(row)

    def commit(self):
        self.commits += 1


class _FakeJob:
    def __init__(self, job_id: int):
        self.id = job_id


def test_persist_worker_run_serializes_dates_to_json_safe_values():
    service = AgenticResearchService()
    fake_db = _FakeDb()
    fake_job = _FakeJob(job_id=123)

    execution = WorkerExecution(
        worker_name="comps_sales",
        status="success",
        data={
            "sale_date": date(2026, 1, 21),
            "nested": {"captured_at": datetime(2026, 2, 6, 12, 34, 56, tzinfo=timezone.utc)},
        },
        unknowns=[{"field": "example", "seen_on": date(2026, 2, 1)}],
        errors=[],
    )

    service._persist_worker_run(db=fake_db, job=fake_job, execution=execution)

    assert fake_db.commits == 1
    assert len(fake_db.rows) == 1
    row = fake_db.rows[0]
    assert row.data["sale_date"] == "2026-01-21"
    assert row.data["nested"]["captured_at"].startswith("2026-02-06T12:34:56")
    assert row.unknowns[0]["seen_on"] == "2026-02-01"
