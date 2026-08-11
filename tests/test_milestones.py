"""Priority 03 — milestone toasts.

Toasts fire once, forever. A duplicate is immediately visible to the user and
cannot be taken back, so the once-only guarantee is worth pinning down.
"""

import tracker_core as core

POLL = core.POLL_INTERVAL


def collect_notifications(tracker):
    seen = []
    tracker.notifier = lambda title, msg: seen.append((title, msg))
    return seen


def accrue(tracker, clock, proc, seconds):
    """Put an app in focus and advance the clock, then flush."""
    for _ in range(2):
        clock.advance(POLL)
        tracker.poll_once(proc, None, clock.monotonic(), clock.time())
    clock.advance(seconds)
    tracker._flush(clock.monotonic())


def test_crossing_a_milestone_notifies_once(tracker, clock):
    seen = collect_notifications(tracker)
    accrue(tracker, clock, 'fl64.exe', 3600)

    assert len(seen) == 1
    title, msg = seen[0]
    assert title == 'Lifetime App Tracker'
    assert '1 hours in FL Studio' in msg


def test_milestone_is_recorded_on_the_entry(tracker, clock):
    collect_notifications(tracker)
    accrue(tracker, clock, 'fl64.exe', 3600)
    assert 1 in tracker.data['fl64.exe']['milestones']


def test_further_time_does_not_re_notify_the_same_milestone(tracker, clock):
    seen = collect_notifications(tracker)
    accrue(tracker, clock, 'fl64.exe', 3600)
    accrue(tracker, clock, 'fl64.exe', 1800)
    assert len(seen) == 1


def test_one_flush_can_cross_several_milestones(tracker, clock):
    seen = collect_notifications(tracker)
    accrue(tracker, clock, 'fl64.exe', 11 * 3600)

    fired = [m for m, _ in ((1, None), (5, None), (10, None))]
    assert len(seen) == len(fired)
    assert '10 hours' in seen[-1][1]


def test_milestones_do_not_re_fire_after_a_restart(storage, clock):
    t1 = core.AppTracker(storage=storage, clock=clock)
    collect_notifications(t1)
    accrue(t1, clock, 'fl64.exe', 3600)
    t1.stop()

    t2 = core.AppTracker(storage=storage, clock=clock)
    seen2 = collect_notifications(t2)
    accrue(t2, clock, 'fl64.exe', 1800)
    assert seen2 == []


def test_alias_is_preferred_in_the_toast(tracker, clock):
    seen = collect_notifications(tracker)
    for _ in range(2):
        clock.advance(POLL)
        tracker.poll_once('fl64.exe', None, clock.monotonic(), clock.time())
    tracker.data['fl64.exe']['alias'] = 'My DAW'
    clock.advance(3600)
    tracker._flush(clock.monotonic())

    assert 'My DAW' in seen[0][1]


def test_a_raising_notifier_does_not_lose_the_milestone(tracker, clock):
    def boom(title, msg):
        raise RuntimeError('toast subsystem down')
    tracker.notifier = boom

    accrue(tracker, clock, 'fl64.exe', 3600)
    # the crossing is still recorded, so it will not fire again later
    assert 1 in tracker.data['fl64.exe']['milestones']


def test_no_notifier_configured_is_safe(tracker, clock):
    tracker.notifier = None
    accrue(tracker, clock, 'fl64.exe', 3600)
    assert 1 in tracker.data['fl64.exe']['milestones']


def test_below_threshold_does_not_notify(tracker, clock):
    seen = collect_notifications(tracker)
    accrue(tracker, clock, 'fl64.exe', 3599)
    assert seen == []
