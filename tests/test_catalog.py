"""Remote name catalog.

The catalog is untrusted input arriving over the network into a process that
runs at Windows login, so most of these tests are about what it is *not*
allowed to do.
"""

import json

import pytest

import tracker_core as core


@pytest.fixture(autouse=True)
def _reset_tables():
    """The catalog mutates module-level tables; restore them after each test."""
    names_before = dict(core.KNOWN_NAMES)
    skips_before = set(core.EXTRA_SKIP_PROCS)
    yield
    core.KNOWN_NAMES.clear()
    core.KNOWN_NAMES.update(names_before)
    core.EXTRA_SKIP_PROCS.clear()
    core.EXTRA_SKIP_PROCS.update(skips_before)


def payload(**kw):
    base = {'version': 1, 'known_names': {}, 'skip_procs': []}
    base.update(kw)
    return base


def opener_returning(obj):
    body = obj if isinstance(obj, (str, bytes)) else json.dumps(obj)
    return lambda url, timeout: body.encode() if isinstance(body, str) else body


# --------------------------------------------------------------------------
# sanitize — happy path
# --------------------------------------------------------------------------
def test_valid_catalog_parses():
    names, skips = core.sanitize_catalog(payload(
        known_names={'cursor.exe': 'Cursor'},
        skip_procs=['noisy.exe'],
    ))
    assert names == {'cursor.exe': 'Cursor'}
    assert skips == {'noisy.exe'}


def test_missing_sections_default_to_empty():
    assert core.sanitize_catalog({'version': 1}) == ({}, set())


def test_process_keys_are_lowercased_and_stripped():
    names, skips = core.sanitize_catalog(payload(
        known_names={'  CURSOR.EXE  ': '  Cursor  '},
        skip_procs=['  NOISY.EXE  '],
    ))
    assert names == {'cursor.exe': 'Cursor'}
    assert skips == {'noisy.exe'}


# --------------------------------------------------------------------------
# sanitize — rejection
# --------------------------------------------------------------------------
@pytest.mark.parametrize('bad', [
    None, [], 'string', 42,
])
def test_non_object_payloads_are_rejected(bad):
    with pytest.raises(ValueError):
        core.sanitize_catalog(bad)


@pytest.mark.parametrize('version', [None, 0, 2, '1', 1.5])
def test_unsupported_versions_are_rejected(version):
    with pytest.raises(ValueError):
        core.sanitize_catalog({'version': version})


def test_wrong_section_types_are_rejected():
    with pytest.raises(ValueError):
        core.sanitize_catalog(payload(known_names=['not', 'an', 'object']))
    with pytest.raises(ValueError):
        core.sanitize_catalog(payload(skip_procs={'not': 'a list'}))


def test_oversized_catalog_is_rejected():
    huge = {f'app{i}.exe': 'X' for i in range(core.CATALOG_MAX_ENTRIES + 1)}
    with pytest.raises(ValueError):
        core.sanitize_catalog(payload(known_names=huge))


# --------------------------------------------------------------------------
# sanitize — junk entries are dropped, not fatal
# --------------------------------------------------------------------------
def test_non_string_entries_are_dropped_individually():
    names, skips = core.sanitize_catalog(payload(
        known_names={'good.exe': 'Good', 'bad.exe': 42, 7: 'Nope'},
        skip_procs=['fine.exe', 99, None],
    ))
    assert names == {'good.exe': 'Good'}
    assert skips == {'fine.exe'}


def test_empty_keys_and_values_are_dropped():
    names, _ = core.sanitize_catalog(payload(
        known_names={'': 'Nameless', 'ok.exe': '', 'good.exe': 'Good'}))
    assert names == {'good.exe': 'Good'}


def test_overlong_entries_are_dropped():
    names, skips = core.sanitize_catalog(payload(
        known_names={
            'x' * (core.CATALOG_MAX_PROC_LEN + 1): 'Long Key',
            'ok.exe': 'y' * (core.CATALOG_MAX_NAME_LEN + 1),
            'good.exe': 'Good',
        },
        skip_procs=['z' * (core.CATALOG_MAX_PROC_LEN + 1), 'fine.exe'],
    ))
    assert names == {'good.exe': 'Good'}
    assert skips == {'fine.exe'}


@pytest.mark.parametrize('evil', [
    'Line\nBreak', 'Tab\there', 'Null\x00byte', 'Carriage\rReturn',
])
def test_control_characters_in_display_names_are_dropped(evil):
    names, _ = core.sanitize_catalog(payload(
        known_names={'bad.exe': evil, 'good.exe': 'Good'}))
    assert names == {'good.exe': 'Good'}


# --------------------------------------------------------------------------
# fetch — transport rules
# --------------------------------------------------------------------------
@pytest.mark.parametrize('url', [
    'http://example.com/c.json',
    'file:///etc/passwd',
    'ftp://example.com/c.json',
    '//example.com/c.json',
    '',
    None,
])
def test_non_https_urls_are_refused(url):
    with pytest.raises(ValueError):
        core.fetch_catalog(url, opener=opener_returning(payload()))


def test_https_url_is_accepted():
    names, _ = core.fetch_catalog(
        'https://example.com/c.json',
        opener=opener_returning(payload(known_names={'a.exe': 'A'})))
    assert names == {'a.exe': 'A'}


def test_oversized_response_is_refused():
    body = b'x' * (core.CATALOG_MAX_BYTES + 1)
    with pytest.raises(ValueError):
        core.fetch_catalog('https://example.com/c.json',
                           opener=lambda url, timeout: body)


def test_malformed_json_raises():
    with pytest.raises(Exception):
        core.fetch_catalog('https://example.com/c.json',
                           opener=opener_returning('{not json'))


# --------------------------------------------------------------------------
# cache
# --------------------------------------------------------------------------
def test_cache_round_trips(tmp_path):
    cache = core.CatalogCache(tmp_path / 'catalog.json')
    assert cache.write({'a.exe': 'A'}, {'b.exe'}) is True
    assert cache.read() == ({'a.exe': 'A'}, {'b.exe'})


def test_missing_cache_reads_none(tmp_path):
    assert core.CatalogCache(tmp_path / 'nope.json').read() is None


def test_corrupt_cache_reads_none(tmp_path):
    p = tmp_path / 'catalog.json'
    p.write_text('{ truncated', encoding='utf-8')
    assert core.CatalogCache(p).read() is None


def test_cache_leaves_no_temp_file(tmp_path):
    cache = core.CatalogCache(tmp_path / 'catalog.json')
    cache.write({'a.exe': 'A'}, set())
    assert list(tmp_path.glob('*.tmp')) == []


# --------------------------------------------------------------------------
# resolve — the fallback chain
# --------------------------------------------------------------------------
def test_resolve_prefers_the_network(tmp_path):
    cache = core.CatalogCache(tmp_path / 'catalog.json')
    cache.write({'old.exe': 'Old'}, set())
    names, _ = core.resolve_catalog(
        cache=cache, url='https://example.com/c.json',
        opener=opener_returning(payload(known_names={'new.exe': 'New'})))
    assert names == {'new.exe': 'New'}


def test_a_successful_fetch_updates_the_cache(tmp_path):
    cache = core.CatalogCache(tmp_path / 'catalog.json')
    core.resolve_catalog(
        cache=cache, url='https://example.com/c.json',
        opener=opener_returning(payload(known_names={'new.exe': 'New'})))
    assert cache.read() == ({'new.exe': 'New'}, set())


def test_resolve_falls_back_to_cache_when_offline(tmp_path):
    cache = core.CatalogCache(tmp_path / 'catalog.json')
    cache.write({'cached.exe': 'Cached'}, set())

    def boom(url, timeout):
        raise OSError('network unreachable')

    names, _ = core.resolve_catalog(cache=cache,
                                    url='https://example.com/c.json',
                                    opener=boom)
    assert names == {'cached.exe': 'Cached'}


def test_a_bad_fetch_does_not_overwrite_a_good_cache(tmp_path):
    cache = core.CatalogCache(tmp_path / 'catalog.json')
    cache.write({'cached.exe': 'Cached'}, set())
    core.resolve_catalog(cache=cache, url='https://example.com/c.json',
                         opener=opener_returning('{ garbage'))
    assert cache.read() == ({'cached.exe': 'Cached'}, set())


def test_resolve_returns_empty_when_everything_fails(tmp_path):
    def boom(url, timeout):
        raise OSError('down')
    cache = core.CatalogCache(tmp_path / 'missing.json')
    assert core.resolve_catalog(cache=cache, url='https://x/c.json',
                                opener=boom) == ({}, set())


def test_resolve_is_a_noop_when_no_url_is_configured(monkeypatch):
    monkeypatch.delenv(core.CATALOG_ENV_VAR, raising=False)
    assert core.resolve_catalog() == ({}, set())


def test_resolve_reads_the_url_from_the_environment(monkeypatch):
    monkeypatch.setenv(core.CATALOG_ENV_VAR, 'https://example.com/c.json')
    assert core.catalog_url() == 'https://example.com/c.json'


def test_resolve_never_raises(tmp_path):
    def boom(url, timeout):
        raise RuntimeError('anything at all')
    # no cache, exploding opener, still returns a usable pair
    assert core.resolve_catalog(cache=None, url='https://x/c.json',
                                opener=boom) == ({}, set())


# --------------------------------------------------------------------------
# apply — what a catalog is allowed to change
# --------------------------------------------------------------------------
def test_apply_adds_a_friendly_name():
    core.apply_catalog({'brandnew.exe': 'Brand New'}, set())
    assert core.resolve_display_name('brandnew.exe') == 'Brand New'


def test_apply_can_correct_an_existing_name():
    core.apply_catalog({'fl64.exe': 'FL Studio 22'}, set())
    assert core.resolve_display_name('fl64.exe') == 'FL Studio 22'


def test_apply_invalidates_the_display_name_cache():
    assert core.resolve_display_name('later.exe') == 'later'
    core.apply_catalog({'later.exe': 'Later Renamed'}, set())
    assert core.resolve_display_name('later.exe') == 'Later Renamed'


def test_catalog_skips_reach_a_new_tracker(storage, clock):
    core.apply_catalog({}, {'noisy.exe'})
    t = core.AppTracker(storage=storage, clock=clock)
    assert 'noisy.exe' in t.skip_procs


def test_a_catalog_skip_stops_new_time_being_recorded(storage, clock):
    core.apply_catalog({}, {'noisy.exe'})
    t = core.AppTracker(storage=storage, clock=clock)
    for _ in range(4):
        clock.advance(core.POLL_INTERVAL)
        t.poll_once('noisy.exe', None, clock.monotonic(), clock.time())
    t._flush(clock.monotonic())
    assert t.data.get('noisy.exe', {}).get('seconds', 0) == 0


def test_a_catalog_skip_never_deletes_existing_user_data(storage, clock):
    """A newly published skip must not wipe time the user already accrued."""
    t1 = core.AppTracker(storage=storage, clock=clock)
    t1.data['noisy.exe'] = core._normalize_entry({'seconds': 50000.0})
    t1.save()

    core.apply_catalog({}, {'noisy.exe'})
    t2 = core.AppTracker(storage=storage, clock=clock)
    assert t2.data['noisy.exe']['seconds'] == 50000.0
    t2.save()
    assert core.Storage(storage.data_dir).load()['noisy.exe']['seconds'] == 50000.0


def test_a_catalog_cannot_unskip_a_built_in_shell_process(storage, clock):
    """The built-in policy list is not editable from the network."""
    core.apply_catalog({'dwm.exe': 'Totally Legit App'}, set())
    t = core.AppTracker(storage=storage, clock=clock)
    assert 'dwm.exe' in t.skip_procs

    for _ in range(4):
        clock.advance(core.POLL_INTERVAL)
        t.poll_once('dwm.exe', None, clock.monotonic(), clock.time())
    t._flush(clock.monotonic())
    assert 'dwm.exe' not in t.data
