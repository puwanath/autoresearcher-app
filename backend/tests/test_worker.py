"""The Celery worker must reuse one event loop per process (module-level async clients are loop-bound)."""

import asyncio

from app import worker


def test_run_sync_reuses_one_loop():
    worker._loop = None
    seen = []

    async def which():
        seen.append(asyncio.get_running_loop())
        return len(seen)

    assert worker._run_sync(which()) == 1
    assert worker._run_sync(which()) == 2
    assert seen[0] is seen[1] and not seen[0].is_closed()
