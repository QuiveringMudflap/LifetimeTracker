# Lifetime App Tracker

A tiny Windows system-tray app that **permanently** tracks how long you spend in every program you use. Think iOS Screen Time, but lifetime — so years from now you can answer "how many hours have I spent in FL Studio?" with an exact number.

- Runs silently in the background (no console window)
- Auto-starts with Windows
- Only adds an app to the list when you actually open it (no list of 500 background services)
- Live-updating dashboard with real app icons and friendly names
- Pauses automatically when you ask, never loses data

## Features

- **Lifetime totals** for every app you focus, persisted to a JSON file in `%APPDATA%`
- **Today / This Week / Lifetime** time-range toggle
- **Real app icons** extracted from each EXE (with letter-avatar fallback)
- **Friendly names** — "FL Studio" instead of `FL64.exe`, "After Effects" instead of `AfterFX.exe`
- **Smart filtering** — ignores cloaked windows, untitled windows, and a long list of Windows shell processes (`dwm.exe`, `SearchHost.exe`, etc.)
- **Pause button** — tray menu or stats window. Existing hours preserved.
- **Right-click any app** → Rename, Hide, or Merge into another group
- **Live search** across your tracked apps
- **Per-app meta** — total sessions and first-seen date
- **Milestone toasts** — Windows notification when you cross 1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, or 10000 hours in a single app
- **Daily rotating backups** of your data file (keeps last 7 days)
- Crash-resilient: saves on every focus change

## Install

Requires Windows + Python 3.10 or newer.

```cmd
git clone https://github.com/<your-username>/LifetimeTracker.git
cd LifetimeTracker
py -m pip install -r requirements.txt
py setup_startup.py
```

`setup_startup.py` registers the tracker in Windows' startup so it runs every time you log in. To start it immediately without rebooting, just double-click `tracker.pyw`.

## Usage

After install, look at your system tray (bottom-right of the taskbar — you may need to click the `^` to show hidden icons). A small purple clock icon will appear.

- **Left-click / "View Stats"** — opens the live dashboard
- **"Pause tracking"** — toggles tracking on/off (use this when you walk away from your PC)
- **"Exit"** — stops the tracker

In the dashboard, **right-click any app row** for Rename / Hide / Merge actions.

## Remote name catalog (optional, off by default)

The two tables that go stale fastest are the friendly-name map and the
skip-list — a new editor ships and needs a display name, a new background
service starts showing up and needs ignoring. Both are just dictionary
entries, so the tracker can fetch them instead of waiting for a reinstall.

Publish a JSON file anywhere reachable over HTTPS:

```json
{
  "version": 1,
  "known_names": { "zed.exe": "Zed", "ghostty.exe": "Ghostty" },
  "skip_procs":  [ "somenewservice.exe" ]
}
```

Then point the tracker at it:

```cmd
setx LIFETIMETRACKER_CATALOG_URL "https://example.com/catalog.json"
```

It's fetched on startup in a background thread, so an unreachable host never
delays the tray icon. The last good copy is cached in
`%APPDATA%\LifetimeTracker\catalog.json` and used when you're offline. With
no URL set, nothing is fetched.

**What a catalog can and cannot do.** It carries data only — nothing in it is
ever executed. It can add or correct display names and add processes to the
skip-list. It cannot remove a built-in skip (which would start tracking a
system process), cannot be served over plain HTTP, and cannot delete usage
you've already recorded: a newly published skip stops *future* time being
counted and leaves your existing totals intact.

Treat the URL as trusted infrastructure. Anyone who can change that file can
change what your tracker displays, so host it somewhere only you can write to.

## Data location

Everything lives in `%APPDATA%\LifetimeTracker\`:

- `app_usage.json` — your lifetime usage data
- `backups/` — last 7 daily snapshots
- `catalog.json` — cached name catalog (only if you've configured one)
- `tracker.log` — error log

## Development

```cmd
py -m pip install -r requirements-dev.txt
py -m pytest
```

`tracker_core.py` holds all the platform-independent logic — persistence, the
tracking clock, grouping and formatting — and has no Windows dependencies, so
the test suite runs on any OS. `tracker.pyw` is the Windows entry point: the
win32 bindings, the Tk dashboard and the tray icon.

To completely reset: delete that folder.

## Uninstall

```cmd
py setup_startup.py --uninstall
```

(or just delete the `LifetimeTracker` registry key under `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).

Then delete the cloned folder and `%APPDATA%\LifetimeTracker\` if you want all data gone.

## License

MIT — see [LICENSE](LICENSE).
