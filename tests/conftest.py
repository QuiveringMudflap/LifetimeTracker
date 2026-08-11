import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tracker_core as core  # noqa: E402


class FakeClock:
    """Deterministic stand-in for SystemClock.

    `monotonic` and `time` advance together but start from different origins,
    mirroring production where elapsed time is monotonic and session-gap
    detection uses a real unix timestamp.
    """

    def __init__(self, mono=1000.0, wall=1_750_000_000.0):
        self._mono = mono
        self._wall = wall
        self.slept = []

    def monotonic(self):
        return self._mono

    def time(self):
        return self._wall

    def sleep(self, secs):
        self.slept.append(secs)
        self.advance(secs)

    def advance(self, secs):
        self._mono += secs
        self._wall += secs


@pytest.fixture(autouse=True)
def _clear_caches():
    """Display-name memoisation is module-global; reset it between tests."""
    core.clear_caches()
    core.set_exe_describer(None)
    yield
    core.clear_caches()
    core.set_exe_describer(None)


@pytest.fixture
def storage(tmp_path):
    s = core.Storage(data_dir=tmp_path)
    s.ensure_dirs()
    return s


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def tracker(storage, clock):
    return core.AppTracker(storage=storage, clock=clock)


@pytest.fixture
def write_data(tmp_path):
    """Write a raw payload to a path under the tmp data dir."""
    def _write(payload, name='app_usage.json', subdir=None):
        target = tmp_path / subdir if subdir else tmp_path
        target.mkdir(parents=True, exist_ok=True)
        path = target / name
        if isinstance(payload, str):
            path.write_text(payload, encoding='utf-8')
        else:
            path.write_text(json.dumps(payload), encoding='utf-8')
        return path
    return _write
