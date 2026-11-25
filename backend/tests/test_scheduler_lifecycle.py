from dataclasses import replace

from app.core.environment import settings
from app.services import scheduler_service


def test_scheduler_start_is_idempotent_and_shutdown_releases_lock(tmp_path, monkeypatch):
    monkeypatch.setattr(
        scheduler_service,
        "settings",
        replace(settings, data_dir=tmp_path, scheduler_enabled=True),
    )

    try:
        assert scheduler_service.start_scheduler() is True
        assert scheduler_service.start_scheduler() is True
        assert {job.id for job in scheduler_service.scheduler.get_jobs()} == {
            "market_scan",
            "review_generation",
        }
    finally:
        scheduler_service.shutdown_scheduler()

    assert scheduler_service.scheduler.running is False
    assert scheduler_service._scheduler_lock_handle is None