"""
Lifetime App Tracker — platform-independent core.

Everything in this module is pure Python: no win32, no ctypes, no tkinter,
and no import-time side effects. Windows-specific behaviour is supplied by
the caller as injectable hooks (see AppTracker's constructor).

tracker.pyw is the Windows entry point that wires this up to the real
foreground-window API, icon extraction and the Tk dashboard.
"""

import json
import logging
import os
import shutil
import threading
import time
from datetime import date, timedelta
from pathlib import Path

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
POLL_INTERVAL    = 5
SAVE_INTERVAL    = 15    # periodic save (also saves on every focus change)
UI_REFRESH_MS    = 1000
ICON_SIZE        = 22
BACKUP_KEEP      = 7
MIN_DWELL_POLLS  = 2     # app must hold focus for this many consecutive polls
                         # (~10s) before it registers — kills taskbar/tray flashes
SESSION_GAP_SECS = 1800  # 30 min gap in focus = new session (not every alt-tab)

# Milestones in hours — toasted when crossed
MILESTONES_HOURS = [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]

DEFAULT_SKIP_PROCS = frozenset({
    'tracker.pyw', 'python.exe', 'pythonw.exe',
    'searchhost.exe', 'textinputhost.exe', 'shellexperiencehost.exe',
    'startmenuexperiencehost.exe', 'lockapp.exe',
    'applicationframehost.exe',
    'dwm.exe', 'sihost.exe', 'csrss.exe', 'winlogon.exe',
    'services.exe', 'svchost.exe', 'dllhost.exe', 'rundll32.exe',
    'conhost.exe', 'werfault.exe', 'dashost.exe', 'ctfmon.exe',
    'runtimebroker.exe', 'smartscreen.exe', 'widgets.exe',
    'searchindexer.exe', 'searchapp.exe', 'searchui.exe',
    'securityhealthservice.exe', 'securityhealthsystray.exe',
    'nissrv.exe', 'msmpeng.exe', 'fontdrvhost.exe',
    'systemsettings.exe',
    'nvcontainer.exe', 'nvidia web helper.exe',
})

KNOWN_NAMES = {
    # creative / media
    'fl64.exe': 'FL Studio', 'fl.exe': 'FL Studio', 'fl32.exe': 'FL Studio',
    'afterfx.exe': 'After Effects', 'afterfxlib.exe': 'After Effects',
    'photoshop.exe': 'Photoshop', 'illustrator.exe': 'Illustrator',
    'premiere.exe': 'Premiere Pro', 'premierepro.exe': 'Premiere Pro',
    'audition.exe': 'Audition', 'animate.exe': 'Animate',
    'mediaencoder.exe': 'Media Encoder', 'lightroom.exe': 'Lightroom',
    'blender.exe': 'Blender', 'obs64.exe': 'OBS Studio', 'obs32.exe': 'OBS Studio',
    'ableton live.exe': 'Ableton Live',
    'resolve.exe': 'DaVinci Resolve', 'figma.exe': 'Figma',
    'krita.exe': 'Krita', 'aseprite.exe': 'Aseprite',
    # browsers
    'chrome.exe': 'Google Chrome', 'firefox.exe': 'Firefox',
    'msedge.exe': 'Microsoft Edge', 'brave.exe': 'Brave',
    'opera.exe': 'Opera', 'arc.exe': 'Arc', 'vivaldi.exe': 'Vivaldi',
    # dev
    'code.exe': 'VS Code', 'cursor.exe': 'Cursor', 'windsurf.exe': 'Windsurf',
    'devenv.exe': 'Visual Studio', 'idea64.exe': 'IntelliJ IDEA',
    'pycharm64.exe': 'PyCharm', 'webstorm64.exe': 'WebStorm',
    'rider64.exe': 'JetBrains Rider', 'clion64.exe': 'CLion',
    'sublime_text.exe': 'Sublime Text', 'notepad++.exe': 'Notepad++',
    'windowsterminal.exe': 'Windows Terminal', 'wt.exe': 'Windows Terminal',
    'powershell.exe': 'PowerShell', 'pwsh.exe': 'PowerShell',
    'cmd.exe': 'Command Prompt', 'wezterm-gui.exe': 'WezTerm',
    'alacritty.exe': 'Alacritty',
    'godot.exe': 'Godot', 'unity.exe': 'Unity Editor', 'unityhub.exe': 'Unity Hub',
    'ue4editor.exe': 'Unreal Engine', 'unrealeditor.exe': 'Unreal Engine',
    # comms
    'discord.exe': 'Discord', 'slack.exe': 'Slack',
    'teams.exe': 'Microsoft Teams', 'ms-teams.exe': 'Microsoft Teams',
    'zoom.exe': 'Zoom', 'whatsapp.exe': 'WhatsApp',
    'telegram.exe': 'Telegram', 'signal.exe': 'Signal',
    # entertainment
    'steam.exe': 'Steam', 'steamwebhelper.exe': 'Steam',
    'spotify.exe': 'Spotify', 'vlc.exe': 'VLC',
    'epicgameslauncher.exe': 'Epic Games',
    'riotclientux.exe': 'Riot Client', 'leagueclientux.exe': 'League of Legends',
    'battle.net.exe': 'Battle.net',
    'roblox.exe': 'Roblox', 'robloxplayerbeta.exe': 'Roblox',
    'minecraft.exe': 'Minecraft',
    # office
    'winword.exe': 'Microsoft Word', 'excel.exe': 'Microsoft Excel',
    'powerpnt.exe': 'Microsoft PowerPoint', 'outlook.exe': 'Microsoft Outlook',
    'onenote.exe': 'Microsoft OneNote', 'onenotem.exe': 'Microsoft OneNote',
    'acrord32.exe': 'Adobe Acrobat Reader', 'acrobat.exe': 'Adobe Acrobat',
    # system
    'explorer.exe': 'File Explorer', 'notepad.exe': 'Notepad',
    'mspaint.exe': 'Paint', 'calculatorapp.exe': 'Calculator',
    'calculator.exe': 'Calculator', 'taskmgr.exe': 'Task Manager',
    'snippingtool.exe': 'Snipping Tool', 'screenclip.exe': 'Snipping Tool',
    'mstsc.exe': 'Remote Desktop',
}


# ---------------------------------------------------------------------------
# Paths — resolved lazily so importing this module never touches the disk
# ---------------------------------------------------------------------------
def default_data_dir():
    """Where the tracker keeps its data. %APPDATA% on Windows, XDG elsewhere."""
    appdata = os.environ.get('APPDATA')
    if appdata:
        return Path(appdata) / 'LifetimeTracker'
    xdg = os.environ.get('XDG_DATA_HOME')
    if xdg:
        return Path(xdg) / 'LifetimeTracker'
    return Path.home() / '.local' / 'share' / 'LifetimeTracker'


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------
def fmt_duration(seconds):
    seconds = int(seconds)
    if seconds < 0:
        # Python floor-divides negatives, which would render -5 as "59m 55s".
        seconds = 0
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h >= 10000:
        return f"{h:,}h {m}m"
    if h > 0:
        return f"{h}h {m}m {s}s"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


def fmt_date(iso):
    if not iso:
        return None
    try:
        d = date.fromisoformat(iso)
        return f"{d.strftime('%b')} {d.day}, {d.year}"
    except Exception:
        return iso


def today_iso():
    return date.today().isoformat()


# ---------------------------------------------------------------------------
# Display name resolution
# ---------------------------------------------------------------------------
_name_cache = {}
_exe_describer = None   # optional callable(exe_path) -> str | None


def set_exe_describer(fn):
    """Install the platform hook that reads an EXE's FileDescription."""
    global _exe_describer
    _exe_describer = fn


def clear_caches():
    """Drop memoised lookups. Tests call this between cases."""
    _name_cache.clear()


def resolve_display_name(proc_name, exe_path=None):
    key = proc_name.lower()
    if key in _name_cache:
        return _name_cache[key]
    name = KNOWN_NAMES.get(key)
    if not name and exe_path and _exe_describer:
        try:
            name = _exe_describer(exe_path)
        except Exception:
            name = None
    if not name:
        stem = proc_name.rsplit('.', 1)[0] if '.' in proc_name else proc_name
        name = stem if stem else proc_name
    _name_cache[key] = name
    return name


def color_for(name, palette):
    h = 0
    for c in name:
        h = (h * 31 + ord(c)) & 0xFFFFFFFF
    return palette[h % len(palette)]


# ---------------------------------------------------------------------------
# Entry schema (v3)
# ---------------------------------------------------------------------------
def _default_entry():
    return {
        'seconds':      0.0,
        'exe':          None,
        'launches':     0,
        'first_seen':   None,
        'last_focused': 0.0,   # unix timestamp — used for session-gap detection
        'buckets':      {},    # {"YYYY-MM-DD": seconds}
        'alias':        None,
        'hidden':       False,
        'milestones':   [],    # hours already toasted
    }


def _normalize_entry(raw, fallback_seconds=0.0):
    e = _default_entry()
    if isinstance(raw, dict):
        e['seconds']    = float(raw.get('seconds', fallback_seconds) or 0)
        e['exe']        = raw.get('exe')
        e['launches']   = int(raw.get('launches', 0) or 0)
        e['first_seen'] = raw.get('first_seen')
        e['buckets']    = dict(raw.get('buckets', {}) or {})
        e['alias']      = raw.get('alias')
        e['hidden']     = bool(raw.get('hidden', False))
        e['milestones']   = list(raw.get('milestones', []) or [])
        e['last_focused'] = float(raw.get('last_focused', 0) or 0)
    else:
        # v1-style raw seconds number
        e['seconds'] = float(raw or 0)
    # Pre-mark already-reached milestones so migrating users don't get spammed
    hours = e['seconds'] / 3600
    for m in MILESTONES_HOURS:
        if hours >= m and m not in e['milestones']:
            e['milestones'].append(m)
    return e


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
class Storage:
    """Owns the data file, its backups, and every read/write path.

    All paths are constructor arguments so tests can point this at a tmp_path
    instead of the real %APPDATA%.
    """

    def __init__(self, data_dir=None, backup_keep=BACKUP_KEEP):
        self.data_dir    = Path(data_dir) if data_dir else default_data_dir()
        self.data_file   = self.data_dir / 'app_usage.json'
        self.backup_dir  = self.data_dir / 'backups'
        self.log_file    = self.data_dir / 'tracker.log'
        self.backup_keep = backup_keep

    def ensure_dirs(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    # -------- backups ----------------------------------------------------
    def rotate_backups(self):
        """Copy current data file to backups/ with today's date; keep last N."""
        if not self.data_file.exists():
            return
        try:
            today = date.today().isoformat()
            dest = self.backup_dir / f'app_usage_{today}.json'
            if not dest.exists():
                shutil.copy2(self.data_file, dest)
            existing = sorted(self.backup_dir.glob('app_usage_*.json'))
            while len(existing) > self.backup_keep:
                try:
                    existing[0].unlink()
                except Exception:
                    pass
                existing = existing[1:]
        except Exception as e:
            log.error('rotate_backups failed: %s', e)

    # -------- load -------------------------------------------------------
    def _load_one_file(self, path, skip_procs):
        """Load and parse a single data file. Returns dict of apps or raises.

        A malformed entry is dropped rather than rejecting the whole file —
        one unreadable record must not cost the user every other app.
        """
        with open(path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        if isinstance(raw, dict) and isinstance(raw.get('apps'), dict):
            items = list(raw['apps'].items())
        elif isinstance(raw, dict):
            items = [(k, v) for k, v in raw.items()
                     if isinstance(v, (int, float, dict))]
        else:
            raise ValueError(f'unsupported data shape: {type(raw).__name__}')
        apps = {}
        for k, v in items:
            try:
                apps[k.lower()] = _normalize_entry(v)
            except Exception as e:
                log.error('dropping unreadable entry %r: %s', k, e)
        return {k: v for k, v in apps.items() if k not in skip_procs}

    def load(self, skip_procs=DEFAULT_SKIP_PROCS):
        """Load usage data, falling back to backups if the primary file is bad."""
        if not self.data_file.exists():
            return {}

        # 1) Try the main data file
        try:
            return self._load_one_file(self.data_file, skip_procs)
        except Exception as e:
            log.error('primary load failed: %s — trying backups', e)

        # 2) Corrupted primary — quarantine it and try the newest backup
        try:
            quarantine = self.data_file.with_suffix(
                f'.json.corrupt-{int(time.time())}'
            )
            shutil.copy2(self.data_file, quarantine)
            log.warning('corrupt data file quarantined to %s', quarantine)
        except Exception:
            pass

        candidates = sorted(self.backup_dir.glob('app_usage_*.json'), reverse=True)
        for backup in candidates:
            try:
                data = self._load_one_file(backup, skip_procs)
                if data:
                    log.warning('restored data from backup %s (%d apps)',
                                backup.name, len(data))
                    return data
            except Exception as e:
                log.error('backup %s unreadable: %s', backup.name, e)
                continue

        # 3) Every source failed — better to start empty than to crash the tray,
        #    but signal loudly in the log so it's obvious what happened
        log.critical('ALL data sources failed to load — starting empty')
        return {}

    # -------- save -------------------------------------------------------
    def save(self, apps):
        # Safety valve — never overwrite an existing non-empty data file with
        # an empty one. Prevents a load failure from silently wiping user data.
        if (not apps and self.data_file.exists()
                and self.data_file.stat().st_size > 32):
            log.critical('refusing to save empty apps dict over existing data')
            return False
        try:
            tmp = self.data_file.with_suffix('.tmp')
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump({'version': 3, 'apps': apps}, f, indent=2, sort_keys=True)
                f.flush()
                os.fsync(f.fileno())     # force to disk before rename
            tmp.replace(self.data_file)
            return True
        except Exception as e:
            log.error('save failed: %s', e)
            return False


# ---------------------------------------------------------------------------
# Clock — injectable so tests can drive time deterministically
# ---------------------------------------------------------------------------
class SystemClock:
    """Real time. `monotonic` measures elapsed; `time` is the wall clock.

    These are deliberately different clocks: elapsed time must never jump when
    the system clock is adjusted, while session-gap detection must survive a
    reboot and therefore has to be a real timestamp.
    """
    # Bound via the module to avoid shadowing `time` inside the class body.
    monotonic = staticmethod(time.monotonic)
    sleep     = staticmethod(time.sleep)
    time      = staticmethod(time.time)


# ---------------------------------------------------------------------------
# Tracker core
# ---------------------------------------------------------------------------
class AppTracker:
    def __init__(self, storage=None, clock=None, focus_provider=None,
                 exe_resolver=None):
        self.storage        = storage or Storage()
        self.clock          = clock or SystemClock()
        self.focus_provider = focus_provider or (lambda: (None, None))
        self.exe_resolver   = exe_resolver

        # Load with the static skip list, then extend it with the user's
        # hidden apps. The order matters: hidden entries must be read out of
        # the file *before* they start being filtered, or their accumulated
        # time would disappear on the next restart.
        self.skip_procs = set(DEFAULT_SKIP_PROCS)
        self.data = self.storage.load(DEFAULT_SKIP_PROCS)
        for proc, info in self.data.items():
            if info.get('hidden'):
                self.skip_procs.add(proc)

        self.lock            = threading.Lock()
        self.running         = True
        self.paused          = False
        self.current_app     = None
        self.current_exe     = None
        self.current_start   = self.clock.monotonic()
        self.last_save       = self.clock.monotonic()
        self.notifier        = None   # callable(title, message)
        # Dwell tracking — prevents taskbar/tray flashes from registering
        self._candidate      = None   # proc being watched
        self._candidate_hits = 0      # consecutive polls it's been foreground
        self.backfill_exes()

    # -------- persistence helpers ----------------------------------------
    def _ensure_entry(self, proc_name):
        if proc_name not in self.data:
            entry = _default_entry()
            entry['first_seen'] = today_iso()
            self.data[proc_name] = entry
        else:
            e = self.data[proc_name]
            if not e.get('first_seen'):
                e['first_seen'] = today_iso()
        return self.data[proc_name]

    def backfill_exes(self):
        if not self.exe_resolver:
            return
        try:
            for proc_name, entry in list(self.data.items()):
                if entry.get('exe'):
                    continue
                found = self.exe_resolver(proc_name)
                if found:
                    entry['exe'] = found
        except Exception as e:
            log.error('backfill_exes failed: %s', e)

    def save(self):
        return self.storage.save(self.data)

    # -------- core clock -------------------------------------------------
    def _flush(self, now):
        if self.current_app and self.current_app not in self.skip_procs:
            elapsed = now - self.current_start
            if elapsed > 0:
                entry = self._ensure_entry(self.current_app)
                pre_secs = entry['seconds']
                entry['seconds'] += elapsed
                d = today_iso()
                entry['buckets'][d] = entry['buckets'].get(d, 0.0) + elapsed
                if self.current_exe and not entry.get('exe'):
                    entry['exe'] = self.current_exe
                self._check_milestones(self.current_app, pre_secs, entry['seconds'])
        self.current_start = now

    def _check_milestones(self, proc_name, pre_secs, new_secs):
        entry = self.data[proc_name]
        hit = entry.setdefault('milestones', [])
        for m in MILESTONES_HOURS:
            m_secs = m * 3600
            if pre_secs < m_secs <= new_secs and m not in hit:
                hit.append(m)
                display = entry.get('alias') or resolve_display_name(
                    proc_name, entry.get('exe')
                )
                if self.notifier:
                    try:
                        self.notifier(
                            'Lifetime App Tracker',
                            f'{m} hours in {display}! 🎉',
                        )
                    except Exception as e:
                        log.error('notify failed: %s', e)

    def poll_once(self, proc_name, exe, now, wall):
        """Process a single foreground-window sample.

        Split out of track_loop so it can be driven directly with a fake
        clock. Caller must hold no lock; this takes it.
        """
        with self.lock:
            if self.paused:
                self.current_start = now
                self._candidate = None
                self._candidate_hits = 0
                return

            # ---- dwell filter: require MIN_DWELL_POLLS consecutive polls ----
            if proc_name == self._candidate:
                self._candidate_hits += 1
            else:
                self._candidate = proc_name
                self._candidate_hits = 1

            # Only commit a switch once the candidate has dwelled long enough
            focus_changed = False
            if (self._candidate_hits >= MIN_DWELL_POLLS
                    and proc_name is not None
                    and proc_name != self.current_app):
                self._flush(now)
                self.current_app = proc_name
                self.current_exe = exe
                focus_changed = True

                entry = self._ensure_entry(proc_name)
                if exe and not entry.get('exe'):
                    entry['exe'] = exe

                # ---- session-gap logic: only count a new session if the
                #      app hasn't had focus in the last SESSION_GAP_SECS ----
                last_f = entry.get('last_focused', 0) or 0
                if wall - last_f > SESSION_GAP_SECS:
                    entry['launches'] = entry.get('launches', 0) + 1

                entry['last_focused'] = wall

            elif (self._candidate_hits >= MIN_DWELL_POLLS
                    and proc_name is None
                    and self.current_app is not None):
                # Sustained idle — the foreground window is one we skip (lock
                # screen, cloaked window) or there is none. Bank what the app
                # legitimately earned and stop the clock, so an unattended
                # machine is not billed to whatever had focus last.
                # The dwell threshold applies here too, so a transient flash
                # to nothing does not disturb an active session.
                self._flush(now)
                self.current_app = None
                self.current_exe = None
                self.storage.save(self.data)
                self.last_save = now

            elif self.current_app:
                # Update last_focused timestamp while app stays in foreground
                entry = self.data.get(self.current_app)
                if entry is not None:
                    entry['last_focused'] = wall

            if focus_changed or now - self.last_save >= SAVE_INTERVAL:
                self._flush(now)
                self.storage.save(self.data)
                self.last_save = now

    def track_loop(self):
        while self.running:
            self.clock.sleep(POLL_INTERVAL)
            proc_name, exe = self.focus_provider()
            self.poll_once(proc_name, exe,
                           self.clock.monotonic(), self.clock.time())

    def snapshot(self):
        with self.lock:
            now = self.clock.monotonic()
            copy = {k: {**v, 'buckets': dict(v.get('buckets', {}))}
                    for k, v in self.data.items()}
            if (not self.paused
                    and self.current_app
                    and self.current_app not in self.skip_procs):
                elapsed = now - self.current_start
                entry = copy.setdefault(self.current_app, _default_entry())
                entry['seconds'] = entry.get('seconds', 0) + elapsed
                d = today_iso()
                entry.setdefault('buckets', {})
                entry['buckets'][d] = entry['buckets'].get(d, 0.0) + elapsed
                if self.current_exe and not entry.get('exe'):
                    entry['exe'] = self.current_exe
            return copy, self.current_app, self.paused

    # -------- state controls --------------------------------------------
    def set_paused(self, paused):
        with self.lock:
            if paused and not self.paused:
                self._flush(self.clock.monotonic())
                self.storage.save(self.data)
                self.paused = True
            elif not paused and self.paused:
                self.current_start = self.clock.monotonic()
                self._candidate = None
                self._candidate_hits = 0
                self.paused = False

    def toggle_pause(self):
        self.set_paused(not self.paused)
        return self.paused

    def set_alias(self, procs, alias):
        with self.lock:
            clean = (alias or '').strip() or None
            for p in procs:
                if p in self.data:
                    self.data[p]['alias'] = clean
            self.storage.save(self.data)

    def set_hidden(self, procs, hidden):
        with self.lock:
            for p in procs:
                if p in self.data:
                    self.data[p]['hidden'] = bool(hidden)
                    if hidden:
                        self.skip_procs.add(p)
                    elif p not in DEFAULT_SKIP_PROCS:
                        # Only lift a skip the user put there. Shell processes
                        # are skipped by policy and stay skipped.
                        self.skip_procs.discard(p)
            self.storage.save(self.data)

    def merge_into(self, source_procs, target_display):
        """Alias all source procs so they render under target_display."""
        with self.lock:
            for p in source_procs:
                if p in self.data:
                    self.data[p]['alias'] = target_display
            self.storage.save(self.data)

    def stop(self):
        with self.lock:
            if self.running:
                self.running = False
                self._flush(self.clock.monotonic())
                self.storage.save(self.data)


# ---------------------------------------------------------------------------
# Grouping / ranges
# ---------------------------------------------------------------------------
def group_by_display(data, include_hidden=False):
    groups = {}
    for proc, info in data.items():
        if info.get('hidden') and not include_hidden:
            continue
        alias = info.get('alias')
        display = alias or resolve_display_name(proc, info.get('exe'))
        g = groups.get(display)
        if g is None:
            g = {
                'display':     display,
                'seconds':     0.0,
                'launches':    0,
                'exe':         None,
                'dominant':    proc,
                'dominant_secs': 0.0,
                'first_seen':  None,
                'procs':       [],
                'buckets':     {},
            }
            groups[display] = g
        secs = info.get('seconds', 0.0)
        g['seconds']  += secs
        g['launches'] += info.get('launches', 0)
        g['procs'].append(proc)
        for day, ds in info.get('buckets', {}).items():
            g['buckets'][day] = g['buckets'].get(day, 0.0) + ds
        fs = info.get('first_seen')
        if fs and (not g['first_seen'] or fs < g['first_seen']):
            g['first_seen'] = fs
        if secs > g['dominant_secs']:
            g['dominant'] = proc
            g['dominant_secs'] = secs
            if info.get('exe'):
                g['exe'] = info.get('exe')
        elif not g['exe'] and info.get('exe'):
            g['exe'] = info.get('exe')
    return groups


def range_seconds(group, rng):
    if rng == 'lifetime':
        return group['seconds']
    today = date.today()
    if rng == 'today':
        return group['buckets'].get(today.isoformat(), 0.0)
    if rng == 'week':
        total = 0.0
        for i in range(7):
            d = today - timedelta(days=i)
            total += group['buckets'].get(d.isoformat(), 0.0)
        return total
    return group['seconds']


def build_visible_rows(data, rng, query=''):
    """Filter + sort the groups the dashboard should show.

    Extracted out of the Tk refresh callback so range and search behaviour
    can be asserted without a display. Returns (rows, total_secs, max_secs)
    where rows is a list of (display, group) sorted descending by time.
    """
    groups = group_by_display(data)
    query = (query or '').strip().lower()
    visible = []
    for display, g in groups.items():
        g['display_seconds'] = range_seconds(g, rng)
        if query and query not in display.lower():
            continue
        if g['display_seconds'] <= 0 and rng != 'lifetime':
            continue
        visible.append((display, g))
    visible.sort(key=lambda x: x[1]['display_seconds'], reverse=True)
    total_secs = sum(g['display_seconds'] for _, g in visible)
    max_secs = visible[0][1]['display_seconds'] if visible else 1
    return visible, total_secs, max_secs
