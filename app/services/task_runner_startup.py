"""Manual task runner startup workaround.

This module provides a way to manually start the task runner
if the automatic startup event isn't working.
"""

import asyncio
from typing import Optional

_task_runner_started = False
_task_runner_task: Optional[asyncio.Task] = None


def ensure_task_runner_started():
    """
    Ensure the task runner is started. Call this from any request handler.

    This is a workaround if the startup_event isn't being called.
    """
    global _task_runner_started, _task_runner_task

    if _task_runner_started:
        return True

    try:
        from app.services.task_runner import run_task_loop
        from app.main import add_background_task

        _task_runner_task = asyncio.create_task(run_task_loop())
        add_background_task(_task_runner_task)
        _task_runner_started = True
        print("✓ Task runner started manually")
        return True
    except Exception as e:
        print(f"❌ Failed to start task runner: {e}")
        return False


def get_task_runner_status() -> dict:
    """Get the status of the task runner."""
    return {
        "started": _task_runner_started,
        "task_running": _task_runner_task is not None and not _task_runner_task.done()
    }
