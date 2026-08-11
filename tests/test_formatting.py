"""Priority 05 — formatting, ranges and colour. Pure functions, no fixtures."""

from datetime import date, timedelta

import pytest

import tracker_core as core


# --------------------------------------------------------------------------
# fmt_duration
# --------------------------------------------------------------------------
@pytest.mark.parametrize('secs,expected', [
    (0,        '0s'),
    (1,        '1s'),
    (59,       '59s'),
    (60,       '1m 0s'),
    (61,       '1m 1s'),
    (3599,     '59m 59s'),
    (3600,     '1h 0m 0s'),
    (3661,     '1h 1m 1s'),
    (86400,    '24h 0m 0s'),
])
def test_fmt_duration_boundaries(secs, expected):
    assert core.fmt_duration(secs) == expected


def test_fmt_duration_truncates_fractional_seconds():
    assert core.fmt_duration(59.9) == '59s'


def test_fmt_duration_uses_comma_form_at_10000_hours():
    # At >=10000h the seconds component is deliberately dropped to keep the
    # column narrow. Locking the threshold down so a refactor can't drift it.
    assert core.fmt_duration(9999 * 3600 + 59 * 60 + 59) == '9999h 59m 59s'
    assert core.fmt_duration(10000 * 3600) == '10,000h 0m'
    assert core.fmt_duration(12345 * 3600 + 30 * 60 + 59) == '12,345h 30m'


@pytest.mark.parametrize('secs', [-1, -5, -3600, -999999])
def test_fmt_duration_clamps_negatives_to_zero(secs):
    # Without the guard Python floor-divides negatives and -5 renders as
    # "59m 55s".
    assert core.fmt_duration(secs) == '0s'


# --------------------------------------------------------------------------
# fmt_date
# --------------------------------------------------------------------------
def test_fmt_date_formats_iso():
    assert core.fmt_date('2026-08-11') == 'Aug 11, 2026'


def test_fmt_date_does_not_zero_pad_day():
    assert core.fmt_date('2026-08-01') == 'Aug 1, 2026'


def test_fmt_date_passes_through_garbage():
    assert core.fmt_date('not-a-date') == 'not-a-date'


def test_fmt_date_none_is_none():
    assert core.fmt_date(None) is None
    assert core.fmt_date('') is None


# --------------------------------------------------------------------------
# range_seconds
# --------------------------------------------------------------------------
def _group_with_days(days_back_to_secs, lifetime=None):
    today = date.today()
    buckets = {
        (today - timedelta(days=d)).isoformat(): s
        for d, s in days_back_to_secs.items()
    }
    return {
        'seconds': lifetime if lifetime is not None else sum(buckets.values()),
        'buckets': buckets,
    }


def test_range_today_reads_only_todays_bucket():
    g = _group_with_days({0: 100.0, 1: 500.0})
    assert core.range_seconds(g, 'today') == 100.0


def test_range_week_covers_today_plus_six_prior_days():
    g = _group_with_days({d: 10.0 for d in range(10)})
    assert core.range_seconds(g, 'week') == 70.0


def test_range_week_excludes_the_seventh_day_back():
    g = _group_with_days({7: 999.0})
    assert core.range_seconds(g, 'week') == 0.0


def test_range_lifetime_ignores_buckets():
    g = _group_with_days({0: 1.0}, lifetime=123456.0)
    assert core.range_seconds(g, 'lifetime') == 123456.0


def test_range_unknown_key_falls_back_to_lifetime():
    g = _group_with_days({0: 1.0}, lifetime=42.0)
    assert core.range_seconds(g, 'nonsense') == 42.0


def test_range_empty_buckets_is_zero():
    g = {'seconds': 5.0, 'buckets': {}}
    assert core.range_seconds(g, 'today') == 0.0
    assert core.range_seconds(g, 'week') == 0.0


# --------------------------------------------------------------------------
# color_for
# --------------------------------------------------------------------------
PALETTE = ['#a', '#b', '#c', '#d']


def test_color_for_is_deterministic():
    assert core.color_for('FL Studio', PALETTE) == core.color_for('FL Studio', PALETTE)


def test_color_for_stays_in_palette():
    for name in ('Chrome', 'VS Code', '', 'ünïcødé', 'x' * 500):
        assert core.color_for(name, PALETTE) in PALETTE


def test_color_for_differs_across_typical_names():
    names = ['Chrome', 'Firefox', 'VS Code', 'Discord', 'Spotify']
    assert len({core.color_for(n, PALETTE) for n in names}) > 1
