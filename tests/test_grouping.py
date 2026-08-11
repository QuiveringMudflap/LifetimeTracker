"""Priority 04 — grouping, aliasing, hiding and merging.

These mutate persisted user data, and hiding also mutates the skip set the
loader filters on — an interaction that used to depend on an invisible
ordering inside AppTracker.__init__.
"""

import tracker_core as core


def entry(**kw):
    e = core._default_entry()
    e.update(kw)
    return e


# --------------------------------------------------------------------------
# display resolution
# --------------------------------------------------------------------------
def test_known_names_win():
    assert core.resolve_display_name('fl64.exe') == 'FL Studio'
    assert core.resolve_display_name('CHROME.EXE') == 'Google Chrome'


def test_unknown_name_falls_back_to_stem():
    assert core.resolve_display_name('weirdapp.exe') == 'weirdapp'


def test_unknown_name_without_extension_is_used_verbatim():
    assert core.resolve_display_name('weirdapp') == 'weirdapp'


def test_exe_describer_is_consulted_for_unknown_names():
    core.set_exe_describer(lambda path: 'Fancy Editor')
    assert core.resolve_display_name('unknown.exe', r'C:\unknown.exe') == 'Fancy Editor'


def test_known_names_beat_the_exe_describer():
    core.set_exe_describer(lambda path: 'Should Not Win')
    assert core.resolve_display_name('fl64.exe', r'C:\fl64.exe') == 'FL Studio'


def test_a_raising_describer_falls_back_to_the_stem():
    def boom(path):
        raise OSError('no version info')
    core.set_exe_describer(boom)
    assert core.resolve_display_name('unknown.exe', r'C:\unknown.exe') == 'unknown'


# --------------------------------------------------------------------------
# grouping
# --------------------------------------------------------------------------
def test_known_names_collapse_variants_into_one_group():
    data = {'fl64.exe': entry(seconds=100.0), 'fl32.exe': entry(seconds=50.0)}
    groups = core.group_by_display(data)
    assert list(groups) == ['FL Studio']
    assert groups['FL Studio']['seconds'] == 150.0


def test_alias_overrides_the_resolved_name():
    data = {'chrome.exe': entry(seconds=10.0, alias='Browser')}
    assert list(core.group_by_display(data)) == ['Browser']


def test_launches_sum_across_the_group():
    data = {'fl64.exe': entry(launches=3), 'fl32.exe': entry(launches=4)}
    assert core.group_by_display(data)['FL Studio']['launches'] == 7


def test_buckets_sum_per_day_across_the_group():
    data = {
        'fl64.exe': entry(buckets={'2026-08-01': 10.0, '2026-08-02': 5.0}),
        'fl32.exe': entry(buckets={'2026-08-01': 7.0}),
    }
    b = core.group_by_display(data)['FL Studio']['buckets']
    assert b == {'2026-08-01': 17.0, '2026-08-02': 5.0}


def test_earliest_first_seen_wins():
    data = {
        'fl64.exe': entry(first_seen='2026-05-01'),
        'fl32.exe': entry(first_seen='2024-01-15'),
    }
    assert core.group_by_display(data)['FL Studio']['first_seen'] == '2024-01-15'


def test_dominant_proc_is_the_one_with_most_time():
    data = {'fl64.exe': entry(seconds=10.0), 'fl32.exe': entry(seconds=900.0)}
    g = core.group_by_display(data)['FL Studio']
    assert g['dominant'] == 'fl32.exe'


def test_icon_comes_from_the_dominant_proc():
    data = {
        'fl64.exe': entry(seconds=10.0, exe=r'C:\fl64.exe'),
        'fl32.exe': entry(seconds=900.0, exe=r'C:\fl32.exe'),
    }
    assert core.group_by_display(data)['FL Studio']['exe'] == r'C:\fl32.exe'


def test_any_available_exe_is_used_when_the_dominant_lacks_one():
    data = {
        'fl64.exe': entry(seconds=900.0),
        'fl32.exe': entry(seconds=10.0, exe=r'C:\fl32.exe'),
    }
    assert core.group_by_display(data)['FL Studio']['exe'] == r'C:\fl32.exe'


def test_hidden_apps_are_excluded_by_default():
    data = {'chrome.exe': entry(seconds=5.0),
            'code.exe': entry(seconds=5.0, hidden=True)}
    assert list(core.group_by_display(data)) == ['Google Chrome']


def test_hidden_apps_can_be_included_explicitly():
    data = {'code.exe': entry(seconds=5.0, hidden=True)}
    assert 'VS Code' in core.group_by_display(data, include_hidden=True)


# --------------------------------------------------------------------------
# tracker-side mutations
# --------------------------------------------------------------------------
def test_set_alias_persists(tracker):
    tracker.data['chrome.exe'] = entry(seconds=1.0)
    tracker.set_alias(['chrome.exe'], 'Browser')
    assert tracker.storage.load()['chrome.exe']['alias'] == 'Browser'


def test_blank_alias_clears_back_to_none(tracker):
    tracker.data['chrome.exe'] = entry(seconds=1.0, alias='Browser')
    tracker.set_alias(['chrome.exe'], '   ')
    assert tracker.data['chrome.exe']['alias'] is None


def test_merge_aliases_every_source_proc(tracker):
    tracker.data['chrome.exe'] = entry(seconds=1.0)
    tracker.data['msedge.exe'] = entry(seconds=1.0)
    tracker.merge_into(['chrome.exe', 'msedge.exe'], 'Browsers')

    groups = core.group_by_display(tracker.data)
    assert list(groups) == ['Browsers']
    assert sorted(groups['Browsers']['procs']) == ['chrome.exe', 'msedge.exe']


def test_hiding_adds_to_the_skip_set_and_persists(tracker):
    tracker.data['code.exe'] = entry(seconds=1.0)
    tracker.set_hidden(['code.exe'], True)

    assert 'code.exe' in tracker.skip_procs
    assert tracker.storage.load()['code.exe']['hidden'] is True


def test_hidden_app_keeps_its_time_across_a_restart(storage, clock):
    """The hide dialog promises the accumulated time is kept. Hiding extends
    the skip set that the loader filters on, so this is the case where a
    regression would silently delete data.
    """
    t1 = core.AppTracker(storage=storage, clock=clock)
    t1.data['code.exe'] = entry(seconds=9999.0)
    t1.set_hidden(['code.exe'], True)

    t2 = core.AppTracker(storage=storage, clock=clock)
    assert t2.data['code.exe']['seconds'] == 9999.0
    assert t2.data['code.exe']['hidden'] is True
    assert 'code.exe' in t2.skip_procs


def test_unhiding_restores_tracking(tracker):
    tracker.data['code.exe'] = entry(seconds=1.0)
    tracker.set_hidden(['code.exe'], True)
    tracker.set_hidden(['code.exe'], False)

    assert 'code.exe' not in tracker.skip_procs
    assert tracker.data['code.exe']['hidden'] is False
    assert 'VS Code' in core.group_by_display(tracker.data)


def test_unhiding_never_drops_a_default_skip_proc(tracker):
    tracker.data['dwm.exe'] = entry(seconds=1.0)
    tracker.set_hidden(['dwm.exe'], False)
    # dwm.exe is skipped by policy, not by the user's hide action
    assert 'dwm.exe' in tracker.skip_procs


def test_hidden_app_stops_accruing_time(storage, clock):
    t1 = core.AppTracker(storage=storage, clock=clock)
    t1.data['code.exe'] = entry(seconds=100.0)
    t1.set_hidden(['code.exe'], True)

    t1.current_app = 'code.exe'
    t1.current_start = clock.monotonic()
    clock.advance(600)
    t1._flush(clock.monotonic())

    assert t1.data['code.exe']['seconds'] == 100.0


# --------------------------------------------------------------------------
# build_visible_rows — logic lifted out of the Tk refresh callback
# --------------------------------------------------------------------------
def test_rows_are_sorted_by_time_descending():
    data = {'chrome.exe': entry(seconds=10.0),
            'code.exe': entry(seconds=500.0),
            'vlc.exe': entry(seconds=100.0)}
    rows, _, _ = core.build_visible_rows(data, 'lifetime')
    assert [d for d, _ in rows] == ['VS Code', 'VLC', 'Google Chrome']


def test_totals_and_max_are_reported():
    data = {'chrome.exe': entry(seconds=10.0), 'code.exe': entry(seconds=90.0)}
    rows, total, mx = core.build_visible_rows(data, 'lifetime')
    assert total == 100.0
    assert mx == 90.0


def test_search_filters_case_insensitively():
    data = {'chrome.exe': entry(seconds=10.0), 'code.exe': entry(seconds=10.0)}
    rows, _, _ = core.build_visible_rows(data, 'lifetime', query='CHROME')
    assert [d for d, _ in rows] == ['Google Chrome']


def test_lifetime_keeps_zero_second_apps():
    data = {'chrome.exe': entry(seconds=0.0)}
    rows, _, _ = core.build_visible_rows(data, 'lifetime')
    assert len(rows) == 1


def test_today_drops_apps_with_no_time_in_range():
    data = {'chrome.exe': entry(seconds=500.0, buckets={'2020-01-01': 500.0})}
    rows, _, _ = core.build_visible_rows(data, 'today')
    assert rows == []


def test_today_keeps_apps_with_time_in_range():
    data = {'chrome.exe': entry(seconds=500.0,
                                buckets={core.today_iso(): 42.0})}
    rows, total, _ = core.build_visible_rows(data, 'today')
    assert len(rows) == 1
    assert total == 42.0


def test_max_secs_defaults_to_one_when_nothing_is_visible():
    rows, total, mx = core.build_visible_rows({}, 'lifetime')
    assert rows == []
    assert total == 0
    assert mx == 1   # guards the bar-width division in the UI
