"""Priority 02 — focus attribution, the dwell filter and session counting.

Both of these mechanisms exist because of a shipped bug (commit 9c476cd:
Explorer ghost tracking and session overcounting), so each has a named
regression test below.
"""

import tracker_core as core

POLL = core.POLL_INTERVAL


def poll(tracker, clock, proc, exe=None, times=1):
    """Advance the clock and feed the tracker one sample per poll."""
    for _ in range(times):
        clock.advance(POLL)
        tracker.poll_once(proc, exe, clock.monotonic(), clock.time())


# --------------------------------------------------------------------------
# dwell filter  (regression: Explorer ghost tracking)
# --------------------------------------------------------------------------
def test_single_poll_flash_never_becomes_current_app(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=3)
    poll(tracker, clock, 'explorer.exe', times=1)
    assert tracker.current_app == 'chrome.exe'
    assert 'explorer.exe' not in tracker.data


def test_two_consecutive_polls_commit_the_switch(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    assert tracker.current_app == 'chrome.exe'


def test_alternating_flashes_never_reach_the_dwell_threshold(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=3)
    for _ in range(6):
        poll(tracker, clock, 'explorer.exe', times=1)
        poll(tracker, clock, 'chrome.exe', times=1)
    assert tracker.current_app == 'chrome.exe'
    assert 'explorer.exe' not in tracker.data


def test_dwell_counter_resets_when_candidate_changes(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    poll(tracker, clock, 'a.exe', times=1)
    poll(tracker, clock, 'b.exe', times=1)
    # neither reached two consecutive polls
    assert tracker.current_app == 'chrome.exe'


# --------------------------------------------------------------------------
# time accrual
# --------------------------------------------------------------------------
def test_time_accrues_to_the_focused_app(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    poll(tracker, clock, 'chrome.exe', times=4)
    tracker._flush(clock.monotonic())
    assert tracker.data['chrome.exe']['seconds'] == 20.0


def test_switching_apps_splits_the_time(tracker, clock):
    # A switch commits on the second consecutive poll, and the dwell interval
    # leading up to it is credited to the outgoing app — the incoming app's
    # clock starts at the moment the switch commits, not when it first
    # appeared in the foreground.
    poll(tracker, clock, 'chrome.exe', times=2)   # chrome becomes current
    poll(tracker, clock, 'chrome.exe', times=2)   # +10s
    poll(tracker, clock, 'code.exe', times=2)     # +10s to chrome, then switch
    clock.advance(30)
    tracker._flush(clock.monotonic())

    assert tracker.data['chrome.exe']['seconds'] == 20.0
    assert tracker.data['code.exe']['seconds'] == 30.0


def test_todays_bucket_matches_total_for_a_single_day(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=6)
    tracker._flush(clock.monotonic())
    entry = tracker.data['chrome.exe']
    assert entry['buckets'][core.today_iso()] == entry['seconds']


def test_first_seen_is_stamped_on_first_focus(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    assert tracker.data['chrome.exe']['first_seen'] == core.today_iso()


def test_exe_is_recorded_on_first_focus(tracker, clock):
    poll(tracker, clock, 'chrome.exe', exe=r'C:\chrome.exe', times=2)
    assert tracker.data['chrome.exe']['exe'] == r'C:\chrome.exe'


def test_skipped_app_accrues_nothing_even_if_it_becomes_current(tracker, clock):
    tracker.current_app = 'dwm.exe'
    tracker.current_start = clock.monotonic()
    clock.advance(600)
    tracker._flush(clock.monotonic())
    assert 'dwm.exe' not in tracker.data


# --------------------------------------------------------------------------
# session counting  (regression: alt-tab overcounting)
# --------------------------------------------------------------------------
def test_first_ever_focus_counts_one_session(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    assert tracker.data['chrome.exe']['launches'] == 1


def test_alt_tabbing_back_within_the_gap_does_not_count_again(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    poll(tracker, clock, 'code.exe', times=2)
    poll(tracker, clock, 'chrome.exe', times=2)
    assert tracker.data['chrome.exe']['launches'] == 1


def test_returning_after_the_session_gap_counts_a_new_session(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    poll(tracker, clock, 'code.exe', times=2)
    clock.advance(core.SESSION_GAP_SECS + 60)
    poll(tracker, clock, 'chrome.exe', times=2)
    assert tracker.data['chrome.exe']['launches'] == 2


def test_repeated_switching_does_not_inflate_sessions(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    for _ in range(20):
        poll(tracker, clock, 'code.exe', times=2)
        poll(tracker, clock, 'chrome.exe', times=2)
    assert tracker.data['chrome.exe']['launches'] == 1
    assert tracker.data['code.exe']['launches'] == 1


def test_last_focused_uses_wall_clock_not_monotonic(tracker, clock):
    """Session-gap detection is only correct because these are different
    clocks — monotonic for elapsed, wall for gaps that must survive a reboot.
    """
    poll(tracker, clock, 'chrome.exe', times=2)
    assert tracker.data['chrome.exe']['last_focused'] == clock.time()
    assert tracker.data['chrome.exe']['last_focused'] > 1_000_000_000


# --------------------------------------------------------------------------
# pause / resume
# --------------------------------------------------------------------------
def test_pause_stops_accrual(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    tracker.set_paused(True)
    before = tracker.data['chrome.exe']['seconds']

    poll(tracker, clock, 'chrome.exe', times=10)
    tracker._flush(clock.monotonic())
    assert tracker.data['chrome.exe']['seconds'] == before


def test_pause_flushes_time_accrued_so_far(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    poll(tracker, clock, 'chrome.exe', times=2)
    tracker.set_paused(True)
    # 2 polls to commit the switch, then 2 more polls of accrual = 10s
    assert tracker.data['chrome.exe']['seconds'] == 10.0


def test_resume_does_not_backdate_the_paused_interval(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    tracker.set_paused(True)
    at_pause = tracker.data['chrome.exe']['seconds']

    clock.advance(3600)
    tracker.set_paused(False)
    poll(tracker, clock, 'chrome.exe', times=2)
    tracker._flush(clock.monotonic())

    assert tracker.data['chrome.exe']['seconds'] == at_pause + 10.0


def test_toggle_pause_reports_new_state(tracker):
    assert tracker.toggle_pause() is True
    assert tracker.toggle_pause() is False


def test_pause_clears_the_dwell_candidate(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=1)
    tracker.set_paused(True)
    tracker.set_paused(False)
    poll(tracker, clock, 'chrome.exe', times=1)
    # the pre-pause poll must not count toward the dwell threshold
    assert tracker.current_app is None


# --------------------------------------------------------------------------
# idle / skipped foreground windows
# --------------------------------------------------------------------------
def test_sustained_idle_is_not_billed_to_the_previous_app(tracker, clock):
    """An 8-hour lock screen used to land entirely on whatever had focus."""
    poll(tracker, clock, 'chrome.exe', times=2)
    poll(tracker, clock, 'chrome.exe', times=2)      # 10s of real use
    poll(tracker, clock, None, times=(8 * 3600) // POLL)
    tracker._flush(clock.monotonic())

    # 10s of use, plus the dwell interval before idle was confirmed
    assert tracker.data['chrome.exe']['seconds'] <= 10.0 + (POLL * POLL)
    assert tracker.current_app is None


def test_a_brief_flash_to_nothing_does_not_break_focus(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    poll(tracker, clock, None, times=1)
    assert tracker.current_app == 'chrome.exe'


def test_returning_after_a_long_idle_counts_a_new_session(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    assert tracker.data['chrome.exe']['launches'] == 1

    poll(tracker, clock, None, times=(2 * 3600) // POLL)
    poll(tracker, clock, 'chrome.exe', times=2)
    assert tracker.data['chrome.exe']['launches'] == 2


def test_idle_time_lands_in_no_bucket(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    poll(tracker, clock, None, times=(4 * 3600) // POLL)
    tracker._flush(clock.monotonic())

    banked = sum(tracker.data['chrome.exe']['buckets'].values())
    assert banked == tracker.data['chrome.exe']['seconds']
    assert banked < 60


def test_none_focus_before_any_app_records_nothing(tracker, clock):
    poll(tracker, clock, None, times=10)
    assert tracker.data == {}
    assert tracker.current_app is None


# --------------------------------------------------------------------------
# snapshot
# --------------------------------------------------------------------------
def test_snapshot_includes_time_not_yet_flushed(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    clock.advance(30)
    data, current, paused = tracker.snapshot()

    assert current == 'chrome.exe'
    assert paused is False
    assert data['chrome.exe']['seconds'] == 30.0
    # the live figure must not have been written back into the real entry
    assert tracker.data['chrome.exe']['seconds'] == 0.0


def test_snapshot_buckets_are_copies(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=4)
    tracker._flush(clock.monotonic())
    data, _, _ = tracker.snapshot()
    data['chrome.exe']['buckets']['2020-01-01'] = 999.0
    assert '2020-01-01' not in tracker.data['chrome.exe']['buckets']


def test_snapshot_while_paused_adds_no_live_time(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    tracker.set_paused(True)
    at_pause = tracker.data['chrome.exe']['seconds']
    clock.advance(600)

    data, _, paused = tracker.snapshot()
    assert paused is True
    assert data['chrome.exe']['seconds'] == at_pause


# --------------------------------------------------------------------------
# lifecycle
# --------------------------------------------------------------------------
def test_stop_flushes_and_persists(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    poll(tracker, clock, 'chrome.exe', times=2)
    tracker.stop()

    assert tracker.running is False
    reloaded = tracker.storage.load()
    assert reloaded['chrome.exe']['seconds'] == 10.0


def test_stop_is_idempotent(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=4)
    tracker.stop()
    first = tracker.data['chrome.exe']['seconds']
    clock.advance(600)
    tracker.stop()
    assert tracker.data['chrome.exe']['seconds'] == first


def test_periodic_save_fires_on_the_save_interval(tracker, clock):
    poll(tracker, clock, 'chrome.exe', times=2)
    assert tracker.storage.data_file.exists()
    tracker.storage.data_file.unlink()

    # stay on one app so no focus-change save occurs
    poll(tracker, clock, 'chrome.exe', times=(core.SAVE_INTERVAL // POLL) + 1)
    assert tracker.storage.data_file.exists()


def test_tracker_reloads_its_own_saved_state(storage, clock):
    t1 = core.AppTracker(storage=storage, clock=clock)
    for _ in range(4):
        clock.advance(POLL)
        t1.poll_once('chrome.exe', None, clock.monotonic(), clock.time())
    t1.stop()

    t2 = core.AppTracker(storage=storage, clock=clock)
    assert t2.data['chrome.exe']['seconds'] == t1.data['chrome.exe']['seconds']
    assert t2.data['chrome.exe']['launches'] == 1
