"""Priority 01 — persistence, migration and crash recovery.

These paths only execute when something has already gone wrong, which is
exactly why they need tests: a regression here costs the user years of data
and produces no visible symptom until it's too late.
"""

import json

import tracker_core as core


# --------------------------------------------------------------------------
# round trip
# --------------------------------------------------------------------------
def test_missing_file_loads_empty(storage):
    assert storage.load() == {}


def test_save_then_load_round_trips(storage):
    apps = {'chrome.exe': core._normalize_entry({'seconds': 3600.0,
                                                 'launches': 4,
                                                 'first_seen': '2026-01-01'})}
    assert storage.save(apps) is True
    loaded = storage.load()
    assert loaded['chrome.exe']['seconds'] == 3600.0
    assert loaded['chrome.exe']['launches'] == 4
    assert loaded['chrome.exe']['first_seen'] == '2026-01-01'


def test_save_writes_version_3_envelope(storage):
    storage.save({'chrome.exe': core._default_entry()})
    raw = json.loads(storage.data_file.read_text(encoding='utf-8'))
    assert raw['version'] == 3
    assert 'chrome.exe' in raw['apps']


def test_save_leaves_no_temp_file_behind(storage):
    storage.save({'chrome.exe': core._default_entry()})
    assert list(storage.data_dir.glob('*.tmp')) == []


def test_keys_are_lowercased_on_load(storage, write_data):
    write_data({'apps': {'Chrome.EXE': {'seconds': 10.0}}})
    assert 'chrome.exe' in storage.load()


def test_skip_procs_are_filtered_on_load(storage, write_data):
    write_data({'apps': {'chrome.exe': {'seconds': 10.0},
                         'dwm.exe': {'seconds': 999.0}}})
    loaded = storage.load()
    assert 'chrome.exe' in loaded
    assert 'dwm.exe' not in loaded


# --------------------------------------------------------------------------
# migration
# --------------------------------------------------------------------------
def test_v1_flat_map_migrates_to_v3(storage, write_data):
    write_data({'chrome.exe': 7200, 'code.exe': 3600.5})
    loaded = storage.load()
    assert loaded['chrome.exe']['seconds'] == 7200.0
    assert loaded['code.exe']['seconds'] == 3600.5
    assert loaded['chrome.exe']['buckets'] == {}
    assert loaded['chrome.exe']['launches'] == 0


def test_v1_migration_premarks_milestones_instead_of_firing_them(storage, write_data):
    """A migrating user with 3000 hours must not receive 10 toasts at once."""
    write_data({'fl64.exe': 3000 * 3600})
    entry = storage.load()['fl64.exe']
    assert entry['milestones'] == [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500]


def test_normalize_fills_defaults_for_partial_entry():
    e = core._normalize_entry({'seconds': 5.0})
    assert e['launches'] == 0
    assert e['exe'] is None
    assert e['hidden'] is False
    assert e['buckets'] == {}
    assert e['last_focused'] == 0.0


def test_normalize_coerces_null_fields():
    e = core._normalize_entry({'seconds': None, 'buckets': None,
                               'milestones': None, 'last_focused': None})
    assert e['seconds'] == 0.0
    assert e['buckets'] == {}
    assert e['milestones'] == []
    assert e['last_focused'] == 0.0


def test_normalize_preserves_existing_milestones():
    e = core._normalize_entry({'seconds': 2 * 3600, 'milestones': [1]})
    assert e['milestones'] == [1]


# --------------------------------------------------------------------------
# corruption recovery
# --------------------------------------------------------------------------
def test_corrupt_primary_falls_back_to_newest_backup(storage, write_data):
    write_data('{ this is not json', name='app_usage.json')
    write_data({'apps': {'chrome.exe': {'seconds': 100.0}}},
               name='app_usage_2026-08-01.json', subdir='backups')
    write_data({'apps': {'chrome.exe': {'seconds': 500.0}}},
               name='app_usage_2026-08-09.json', subdir='backups')

    loaded = storage.load()
    # newest backup wins (reverse-sorted by ISO date in the filename)
    assert loaded['chrome.exe']['seconds'] == 500.0


def test_corrupt_primary_is_quarantined_not_deleted(storage, write_data):
    write_data('{ truncated', name='app_usage.json')
    write_data({'apps': {'chrome.exe': {'seconds': 1.0}}},
               name='app_usage_2026-08-09.json', subdir='backups')

    storage.load()
    quarantined = list(storage.data_dir.glob('app_usage.json.corrupt-*'))
    assert len(quarantined) == 1
    assert quarantined[0].read_text(encoding='utf-8') == '{ truncated'
    # the original is left in place so the next save can replace it atomically
    assert storage.data_file.exists()


def test_unreadable_backups_are_skipped_until_one_parses(storage, write_data):
    write_data('nope', name='app_usage.json')
    write_data('also nope', name='app_usage_2026-08-09.json', subdir='backups')
    write_data({'apps': {'code.exe': {'seconds': 42.0}}},
               name='app_usage_2026-08-08.json', subdir='backups')

    assert storage.load()['code.exe']['seconds'] == 42.0


def test_empty_backup_is_not_accepted_as_recovery(storage, write_data):
    write_data('bad', name='app_usage.json')
    write_data({'apps': {}}, name='app_usage_2026-08-09.json', subdir='backups')
    write_data({'apps': {'code.exe': {'seconds': 9.0}}},
               name='app_usage_2026-08-08.json', subdir='backups')

    assert storage.load()['code.exe']['seconds'] == 9.0


def test_all_sources_failing_returns_empty_rather_than_raising(storage, write_data):
    write_data('bad', name='app_usage.json')
    write_data('bad', name='app_usage_2026-08-09.json', subdir='backups')
    assert storage.load() == {}


def test_one_malformed_entry_does_not_cost_the_whole_file(storage, write_data):
    """A non-numeric 'seconds' used to raise out of _normalize_entry and
    discard every other app in the file — a total loss when no backup exists.
    """
    write_data({'apps': {'good.exe': {'seconds': 100.0},
                         'bad.exe': {'seconds': 'not-a-number'},
                         'other.exe': {'seconds': 50.0}}})
    loaded = storage.load()
    assert loaded['good.exe']['seconds'] == 100.0
    assert loaded['other.exe']['seconds'] == 50.0
    assert 'bad.exe' not in loaded


def test_many_good_entries_survive_one_bad_one(storage, write_data):
    apps = {f'app{i}.exe': {'seconds': 3600.0} for i in range(500)}
    apps['weird.exe'] = {'seconds': 'not-a-number'}
    write_data({'apps': apps})
    assert len(storage.load()) == 500


def test_a_non_dict_payload_is_still_a_hard_failure(storage, write_data):
    # A JSON list is not a data shape we can interpret; it must fall through
    # to the backup path rather than silently yielding an empty dict.
    write_data([1, 2, 3])
    assert storage.load() == {}
    assert list(storage.data_dir.glob('app_usage.json.corrupt-*'))


# --------------------------------------------------------------------------
# the empty-overwrite safety valve
# --------------------------------------------------------------------------
def test_refuses_to_overwrite_existing_data_with_empty_dict(storage):
    storage.save({'chrome.exe': core._normalize_entry({'seconds': 3600.0})})
    before = storage.data_file.read_text(encoding='utf-8')

    assert storage.save({}) is False
    assert storage.data_file.read_text(encoding='utf-8') == before


def test_empty_save_is_allowed_when_no_data_file_exists(storage):
    assert storage.save({}) is True
    assert storage.data_file.exists()


# --------------------------------------------------------------------------
# backup rotation
# --------------------------------------------------------------------------
def test_rotate_is_a_noop_without_a_data_file(storage):
    storage.rotate_backups()
    assert list(storage.backup_dir.glob('*.json')) == []


def test_rotate_creates_todays_backup(storage):
    storage.save({'chrome.exe': core._default_entry()})
    storage.rotate_backups()
    assert len(list(storage.backup_dir.glob('app_usage_*.json'))) == 1


def test_rotate_twice_in_one_day_does_not_duplicate(storage):
    storage.save({'chrome.exe': core._default_entry()})
    storage.rotate_backups()
    storage.rotate_backups()
    assert len(list(storage.backup_dir.glob('app_usage_*.json'))) == 1


def test_rotate_prunes_to_backup_keep_oldest_first(tmp_path, write_data):
    s = core.Storage(data_dir=tmp_path, backup_keep=3)
    s.ensure_dirs()
    s.save({'chrome.exe': core._default_entry()})
    for day in ('01', '02', '03', '04', '05'):
        write_data({'apps': {}}, name=f'app_usage_2026-08-{day}.json',
                   subdir='backups')

    s.rotate_backups()
    names = sorted(p.name for p in s.backup_dir.glob('app_usage_*.json'))
    assert len(names) == 3
    # oldest are dropped; today's newly written backup survives
    assert 'app_usage_2026-08-01.json' not in names
    assert 'app_usage_2026-08-02.json' not in names
