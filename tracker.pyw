"""
Lifetime App Tracker — Windows entry point.

Sits in the system tray and permanently accumulates how long each app has focus.
Right-click the tray icon -> View Stats to see your lifetime totals.
Data lives in %APPDATA%\\LifetimeTracker\\app_usage.json and never resets.

All platform-independent logic lives in tracker_core.py. This file holds the
Windows API bindings, the Tk dashboard and the tray plumbing.
"""

import atexit
import ctypes
from ctypes import wintypes
import logging
import math
import os
import sys
import threading
import tkinter as tk
import winreg

import win32api
import win32con
import win32gui
import win32process
import win32ui
import psutil
import pystray
from PIL import Image, ImageDraw, ImageFont, ImageTk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tracker_core import (  # noqa: E402
    ICON_SIZE, MILESTONES_HOURS, UI_REFRESH_MS,
    AppTracker, Storage,
    build_visible_rows, color_for, fmt_date, fmt_duration,
    resolve_display_name, set_exe_describer,
)

# ---------------------------------------------------------------------------
# Active window detection
# ---------------------------------------------------------------------------
_dwm = None
_DWMWA_CLOAKED = 14


def _is_cloaked(hwnd):
    val = ctypes.c_int(0)
    try:
        _dwm.DwmGetWindowAttribute(
            wintypes.HWND(hwnd), _DWMWA_CLOAKED,
            ctypes.byref(val), ctypes.sizeof(val),
        )
    except OSError:
        return False
    return val.value != 0


def make_focus_provider(skip_procs):
    """Return a callable() -> (proc_name, exe_path) for the foreground window."""
    def get_active_process():
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd or not win32gui.IsWindowVisible(hwnd):
                return None, None
            if _is_cloaked(hwnd):
                return None, None
            title = win32gui.GetWindowText(hwnd) or ''
            if not title.strip():
                return None, None

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid <= 0:
                return None, None
            proc = psutil.Process(pid)
            name = proc.name().lower()
            if name in skip_procs:
                return None, None
            exe = None
            try:
                exe = proc.exe()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            return name, exe
        except Exception:
            return None, None
    return get_active_process


# ---------------------------------------------------------------------------
# Display name resolution (Windows half)
# ---------------------------------------------------------------------------
def _file_description(exe_path):
    try:
        info = win32api.GetFileVersionInfo(exe_path, '\\VarFileInfo\\Translation')
        if not info:
            return None
        lang, codepage = info[0]
        key = f'\\StringFileInfo\\{lang:04x}{codepage:04x}\\FileDescription'
        desc = win32api.GetFileVersionInfo(exe_path, key)
        return desc.strip() if desc else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Icon extraction + letter avatar fallback
# ---------------------------------------------------------------------------
def _extract_icon_pil(exe_path):
    if not exe_path or not os.path.isfile(exe_path):
        return None
    try:
        large, small = win32gui.ExtractIconEx(exe_path, 0)
        hicon = None
        leftovers = []
        if large:
            hicon = large[0]
            leftovers = list(large[1:]) + list(small)
        elif small:
            hicon = small[0]
            leftovers = list(small[1:])
        else:
            return None
        ico = 32
        hdc_screen = win32gui.GetDC(0)
        try:
            hdc = win32ui.CreateDCFromHandle(hdc_screen)
            hbmp = win32ui.CreateBitmap()
            hbmp.CreateCompatibleBitmap(hdc, ico, ico)
            hdc_mem = hdc.CreateCompatibleDC()
            old = hdc_mem.SelectObject(hbmp)
            win32gui.DrawIconEx(
                hdc_mem.GetSafeHdc(), 0, 0, hicon,
                ico, ico, 0, None, win32con.DI_NORMAL,
            )
            info = hbmp.GetInfo()
            bits = hbmp.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGBA', (info['bmWidth'], info['bmHeight']),
                bits, 'raw', 'BGRA', 0, 1,
            )
            hdc_mem.SelectObject(old)
            hdc_mem.DeleteDC()
            hdc.DeleteDC()
        finally:
            win32gui.ReleaseDC(0, hdc_screen)
            win32gui.DestroyIcon(hicon)
            for h in leftovers:
                try:
                    win32gui.DestroyIcon(h)
                except Exception:
                    pass
        return img
    except Exception as e:
        logging.warning('icon extraction failed for %s: %s', exe_path, e)
        return None


_font_cache = {}


def _get_font(size_px):
    if size_px in _font_cache:
        return _font_cache[size_px]
    font = None
    for candidate in ('segoeuib.ttf', 'seguisb.ttf', 'segoeui.ttf',
                      'arialbd.ttf', 'arial.ttf'):
        try:
            font = ImageFont.truetype(candidate, size_px)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()
    _font_cache[size_px] = font
    return font


def make_letter_icon(display_name, size, bg_color):
    letter = (display_name[:1] or '?').upper()
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    radius = max(3, size // 5)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=bg_color)
    font = _get_font(int(size * 0.58))
    try:
        bbox = d.textbbox((0, 0), letter, font=font)
    except Exception:
        bbox = (0, 0, size // 2, size // 2)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (size - tw) // 2 - bbox[0]
    y = (size - th) // 2 - bbox[1]
    d.text((x, y), letter, fill='white', font=font)
    return img


# ---------------------------------------------------------------------------
# EXE discovery
# ---------------------------------------------------------------------------
_exe_lookup_cache = {}


def find_exe_in_registry(exe_name):
    subkey = rf'Software\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}'
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(hive, subkey) as k:
                val, _ = winreg.QueryValueEx(k, '')
                if val:
                    val = os.path.expandvars(val.strip('"'))
                    if os.path.isfile(val):
                        return val
                try:
                    pth, _ = winreg.QueryValueEx(k, 'Path')
                    candidate = os.path.join(pth, exe_name)
                    if os.path.isfile(candidate):
                        return candidate
                except FileNotFoundError:
                    pass
        except FileNotFoundError:
            continue
        except OSError:
            continue
    return None


def find_exe_in_running(exe_name):
    name_l = exe_name.lower()
    try:
        for proc in psutil.process_iter(['name']):
            try:
                if (proc.info.get('name') or '').lower() == name_l:
                    return proc.exe()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
    except Exception:
        pass
    return None


def resolve_exe(proc_name, known_exe=None):
    if known_exe and os.path.isfile(known_exe):
        return known_exe
    key = proc_name.lower()
    if key in _exe_lookup_cache:
        return _exe_lookup_cache[key]
    found = find_exe_in_running(proc_name) or find_exe_in_registry(proc_name)
    _exe_lookup_cache[key] = found
    return found


# ---------------------------------------------------------------------------
# Stats Window
# ---------------------------------------------------------------------------
BG        = '#0b0720'
CARD      = '#17112e'
CARD_HI   = '#221848'
ACCENT    = '#c084fc'
ACCENT_2  = '#f472b6'
CYAN      = '#22d3ee'
TEXT      = '#ece8ff'
MUTED     = '#8b83a8'
BORDER    = '#2a1f52'
BAR_BG    = '#1d1540'
PAUSE_FG  = '#fbbf24'
PAUSE_BG  = '#3a2a08'
RESUME_FG = '#4ade80'
RESUME_BG = '#0f2a18'

DOT_PALETTE = [
    '#c084fc', '#f472b6', '#22d3ee', '#34d399', '#fbbf24',
    '#fb7185', '#60a5fa', '#a78bfa', '#f59e0b', '#10b981',
    '#e879f9', '#38bdf8', '#4ade80', '#facc15', '#fda4af',
]


def dot_color(name):
    return color_for(name, DOT_PALETTE)


def show_stats_window(tracker):
    root = tk.Tk()
    root.title('Lifetime App Tracker')
    root.geometry('960x720')
    root.minsize(820, 560)
    root.configure(bg=BG)

    alive      = [True]
    rows       = {}        # display -> row widgets
    photo_refs = {}        # display -> PhotoImage
    last_order = [None]
    range_mode = ['lifetime']

    search_var = tk.StringVar(value='')

    # ---- Header ----
    header = tk.Frame(root, bg=BG)
    header.pack(fill=tk.X, padx=28, pady=(22, 6))

    title_row = tk.Frame(header, bg=BG)
    title_row.pack(fill=tk.X)
    tk.Label(title_row, text='Lifetime',
             font=('Segoe UI', 26, 'bold'), bg=BG, fg=TEXT).pack(side=tk.LEFT)
    tk.Label(title_row, text='App Tracker',
             font=('Segoe UI Light', 26), bg=BG, fg=ACCENT
             ).pack(side=tk.LEFT, padx=(10, 0))

    # pill + pause
    pill_row = tk.Frame(header, bg=BG)
    pill_row.pack(fill=tk.X, pady=(10, 0))
    pill = tk.Frame(pill_row, bg=CARD)
    pill.pack(side=tk.LEFT, ipadx=14, ipady=7)
    pill_dot = tk.Label(pill, text='●', font=('Segoe UI', 12, 'bold'),
                        bg=CARD, fg=ACCENT_2)
    pill_dot.pack(side=tk.LEFT, padx=(12, 0))
    pill_text = tk.Label(pill, text='Now tracking: —',
                         font=('Segoe UI Semibold', 10), bg=CARD, fg=TEXT)
    pill_text.pack(side=tk.LEFT, padx=(8, 12))

    pause_btn = tk.Label(pill_row, text='', font=('Segoe UI Semibold', 10),
                         bg=CARD, fg=TEXT, cursor='hand2')
    pause_btn.pack(side=tk.LEFT, padx=(10, 0), ipadx=14, ipady=7)

    def paint_pause(paused):
        if paused:
            pause_btn.configure(text='▶  Resume tracking',
                                bg=RESUME_BG, fg=RESUME_FG)
        else:
            pause_btn.configure(text='⏸  Pause tracking',
                                bg=PAUSE_BG, fg=PAUSE_FG)

    def toggle_pause(_=None):
        tracker.toggle_pause()
        paint_pause(tracker.paused)
    pause_btn.bind('<Button-1>', toggle_pause)
    paint_pause(tracker.paused)

    # tiles
    tiles = tk.Frame(header, bg=BG)
    tiles.pack(fill=tk.X, pady=(16, 8))

    def mk_tile(parent, label, accent):
        wrap = tk.Frame(parent, bg=CARD)
        wrap.pack(side=tk.LEFT, padx=(0, 12), ipadx=18, ipady=12)
        val = tk.Label(wrap, text='—', font=('Segoe UI', 18, 'bold'),
                       bg=CARD, fg=accent)
        val.pack(anchor='w')
        lbl = tk.Label(wrap, text=label.upper(), font=('Segoe UI', 8, 'bold'),
                       bg=CARD, fg=MUTED)
        lbl.pack(anchor='w', pady=(2, 0))
        return val, lbl

    total_val, total_lbl = mk_tile(tiles, 'Total Time',   ACCENT)
    apps_val,  _         = mk_tile(tiles, 'Apps Tracked', CYAN)
    top_val,   _         = mk_tile(tiles, 'Most Used',    ACCENT_2)

    # range + search
    tools = tk.Frame(root, bg=BG)
    tools.pack(fill=tk.X, padx=28, pady=(8, 6))

    range_frame = tk.Frame(tools, bg=BG)
    range_frame.pack(side=tk.LEFT)

    range_buttons = {}

    def paint_range():
        for key, btn in range_buttons.items():
            if key == range_mode[0]:
                btn.configure(bg=ACCENT, fg='white')
            else:
                btn.configure(bg=CARD, fg=MUTED)

    def set_range(key):
        range_mode[0] = key
        last_order[0] = None   # force re-grid in refresh
        paint_range()

    for key, label in (('today', 'Today'), ('week', 'This Week'),
                       ('lifetime', 'Lifetime')):
        b = tk.Label(range_frame, text=label, font=('Segoe UI Semibold', 10),
                     bg=CARD, fg=MUTED, cursor='hand2')
        b.pack(side=tk.LEFT, padx=(0, 6), ipadx=16, ipady=7)
        b.bind('<Button-1>', lambda e, k=key: set_range(k))
        range_buttons[key] = b
    paint_range()

    search_wrap = tk.Frame(tools, bg=CARD)
    search_wrap.pack(side=tk.RIGHT, ipady=4)
    tk.Label(search_wrap, text='🔍', bg=CARD, fg=MUTED,
             font=('Segoe UI', 11)).pack(side=tk.LEFT, padx=(10, 4))
    search_entry = tk.Entry(search_wrap, textvariable=search_var,
                            bg=CARD, fg=TEXT, insertbackground=TEXT,
                            bd=0, relief='flat', font=('Segoe UI', 10),
                            width=24)
    search_entry.pack(side=tk.LEFT, padx=(0, 12), ipady=4)

    def on_search_change(*_):
        last_order[0] = None
    search_var.trace_add('write', on_search_change)

    tk.Frame(root, bg=BORDER, height=1).pack(fill=tk.X, padx=28, pady=(8, 0))

    # ---- Scrollable list ----
    list_wrap = tk.Frame(root, bg=BG)
    list_wrap.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 6))

    canvas = tk.Canvas(list_wrap, bg=BG, highlightthickness=0, bd=0)
    vsb = tk.Scrollbar(list_wrap, orient='vertical', command=canvas.yview,
                       bg=BG, troughcolor=BG, activebackground=ACCENT,
                       bd=0, highlightthickness=0, width=12)
    inner = tk.Frame(canvas, bg=BG)
    inner.columnconfigure(0, weight=1)

    inner_id = canvas.create_window((0, 0), window=inner, anchor='nw')
    canvas.configure(yscrollcommand=vsb.set)
    inner.bind('<Configure>', lambda _: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>', lambda e: canvas.itemconfig(inner_id, width=e.width))
    canvas.bind_all('<MouseWheel>', lambda e: canvas.yview_scroll(int(-e.delta / 120), 'units'))

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)

    BAR_W, BAR_H = 200, 6

    def icon_for(display, proc_name, exe_path):
        if display in photo_refs:
            return photo_refs[display]
        pil = _extract_icon_pil(exe_path) if exe_path else None
        if pil is None:
            resolved = resolve_exe(proc_name, exe_path)
            if resolved:
                pil = _extract_icon_pil(resolved)
        if pil is None:
            pil = make_letter_icon(display, ICON_SIZE, dot_color(display))
        if pil.size != (ICON_SIZE, ICON_SIZE):
            pil = pil.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)
        photo = ImageTk.PhotoImage(pil)
        photo_refs[display] = photo
        return photo

    # ---- dialogs ----
    def open_dialog(title, width=380, height=180):
        dlg = tk.Toplevel(root)
        dlg.title(title)
        dlg.geometry(f'{width}x{height}')
        dlg.configure(bg=BG)
        dlg.transient(root)
        dlg.grab_set()
        dlg.resizable(False, False)
        return dlg

    def mk_dialog_btn(parent, text, fg, bg, cmd):
        b = tk.Label(parent, text=text, bg=bg, fg=fg, cursor='hand2',
                     font=('Segoe UI Semibold', 10))
        b.pack(side=tk.LEFT, padx=4, ipadx=18, ipady=7)
        b.bind('<Button-1>', lambda _e: cmd())
        return b

    def do_rename(display, group):
        dlg = open_dialog(f'Rename "{display}"', 420, 190)
        tk.Label(dlg, text=f'New display name for "{display}":',
                 bg=BG, fg=TEXT, font=('Segoe UI', 10)
                 ).pack(padx=22, pady=(22, 8), anchor='w')
        e = tk.Entry(dlg, bg=CARD, fg=TEXT, insertbackground=TEXT,
                     font=('Segoe UI', 11), bd=0, relief='flat')
        e.pack(padx=22, fill=tk.X, ipady=8)
        e.insert(0, display)
        e.focus_set()
        e.select_range(0, tk.END)

        btns = tk.Frame(dlg, bg=BG)
        btns.pack(pady=18)

        def apply():
            new = e.get().strip()
            if new and new != display:
                tracker.set_alias(group['procs'], new)
                # remove old row immediately (refresh will rebuild under new key)
                if display in rows:
                    rows[display]['frame'].destroy()
                    rows.pop(display, None)
                photo_refs.pop(display, None)
                last_order[0] = None
            dlg.destroy()

        mk_dialog_btn(btns, 'Rename', 'white', ACCENT, apply)
        mk_dialog_btn(btns, 'Cancel', TEXT, CARD, dlg.destroy)
        e.bind('<Return>', lambda _e: apply())
        e.bind('<Escape>', lambda _e: dlg.destroy())

    def do_hide(display, group):
        dlg = open_dialog('Hide app?', 440, 200)
        tk.Label(dlg,
                 text=f'Hide "{display}" from the list and stop tracking it?',
                 bg=BG, fg=TEXT, font=('Segoe UI', 10), wraplength=400,
                 justify='left').pack(padx=22, pady=(22, 4), anchor='w')
        tk.Label(dlg, text='Its accumulated time is kept in the data file.',
                 bg=BG, fg=MUTED, font=('Segoe UI', 9)
                 ).pack(padx=22, anchor='w')

        btns = tk.Frame(dlg, bg=BG)
        btns.pack(pady=18)

        def apply():
            tracker.set_hidden(group['procs'], True)
            if display in rows:
                rows[display]['frame'].destroy()
                rows.pop(display, None)
            photo_refs.pop(display, None)
            last_order[0] = None
            dlg.destroy()

        mk_dialog_btn(btns, 'Hide', 'white', '#dc2626', apply)
        mk_dialog_btn(btns, 'Cancel', TEXT, CARD, dlg.destroy)

    def do_merge(source_display, source_group, all_groups):
        candidates = [d for d in all_groups.keys() if d != source_display]
        if not candidates:
            return
        dlg = open_dialog(f'Merge "{source_display}" into…', 420, 360)
        tk.Label(dlg,
                 text=f'Combine "{source_display}" into another app:',
                 bg=BG, fg=TEXT, font=('Segoe UI', 10)
                 ).pack(padx=22, pady=(22, 8), anchor='w')

        list_frame = tk.Frame(dlg, bg=CARD)
        list_frame.pack(padx=22, fill=tk.BOTH, expand=True)

        lb = tk.Listbox(list_frame, bg=CARD, fg=TEXT,
                        selectbackground=ACCENT, selectforeground='white',
                        bd=0, relief='flat', highlightthickness=0,
                        font=('Segoe UI', 10), activestyle='none')
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        for d in sorted(candidates, key=str.lower):
            lb.insert(tk.END, f'  {d}')
        lb.selection_set(0)

        btns = tk.Frame(dlg, bg=BG)
        btns.pack(pady=14)

        def apply():
            sel = lb.curselection()
            if not sel:
                dlg.destroy()
                return
            target = lb.get(sel[0]).strip()
            tracker.merge_into(source_group['procs'], target)
            if source_display in rows:
                rows[source_display]['frame'].destroy()
                rows.pop(source_display, None)
            photo_refs.pop(source_display, None)
            photo_refs.pop(target, None)     # rebuild target icon from new dominant
            last_order[0] = None
            dlg.destroy()

        mk_dialog_btn(btns, 'Merge', 'white', ACCENT, apply)
        mk_dialog_btn(btns, 'Cancel', TEXT, CARD, dlg.destroy)
        lb.bind('<Double-Button-1>', lambda _e: apply())

    # ---- row factory ----
    def make_row(display, group):
        accent = dot_color(display)
        f = tk.Frame(inner, bg=CARD)
        f.columnconfigure(2, weight=1)

        rank_lbl = tk.Label(f, text='', font=('Consolas', 11, 'bold'),
                            bg=CARD, fg=MUTED, width=3, anchor='e')
        rank_lbl.grid(row=0, column=0, rowspan=2, padx=(18, 14), pady=14, sticky='nsw')

        photo = icon_for(display, group['dominant'], group['exe'])
        icon_lbl = tk.Label(f, image=photo, bg=CARD, bd=0)
        icon_lbl.image = photo
        icon_lbl.grid(row=0, column=1, rowspan=2, padx=(0, 12))

        name_lbl = tk.Label(f, text=display,
                            font=('Segoe UI Semibold', 11),
                            bg=CARD, fg=TEXT, anchor='w')
        name_lbl.grid(row=0, column=2, sticky='ew', pady=(12, 0))

        meta_lbl = tk.Label(f, text='', font=('Segoe UI', 8),
                            bg=CARD, fg=MUTED, anchor='w')
        meta_lbl.grid(row=1, column=2, sticky='ew', pady=(0, 12))

        time_lbl = tk.Label(f, text='', font=('Consolas', 11, 'bold'),
                            bg=CARD, fg=ACCENT, anchor='e')
        time_lbl.grid(row=0, column=3, rowspan=2, padx=(12, 16))

        bar_frame = tk.Frame(f, bg=CARD)
        bar_frame.grid(row=0, column=4, rowspan=2, padx=(0, 18))
        bar_cv = tk.Canvas(bar_frame, width=BAR_W, height=BAR_H,
                           bg=BAR_BG, highlightthickness=0, bd=0)
        bar_cv.pack()
        bar_id = bar_cv.create_rectangle(0, 0, 0, BAR_H, fill=accent, outline='')

        pct_lbl = tk.Label(f, text='', font=('Segoe UI', 9),
                           bg=CARD, fg=MUTED, width=6, anchor='e')
        pct_lbl.grid(row=0, column=5, rowspan=2, padx=(0, 18))

        r = {
            'frame': f, 'rank': rank_lbl, 'icon': icon_lbl,
            'name': name_lbl, 'meta': meta_lbl,
            'time': time_lbl, 'bar_cv': bar_cv, 'bar_id': bar_id,
            'bar_frame': bar_frame, 'pct': pct_lbl,
        }

        # Right-click context menu
        def bind_ctx(w, display=display):
            def popup(event):
                menu = tk.Menu(root, tearoff=0, bg=CARD, fg=TEXT,
                               activebackground=ACCENT,
                               activeforeground='white', bd=0)
                cur_row = rows.get(display)
                g = cur_row.get('group') if cur_row else None
                if g is None:
                    return
                menu.add_command(label='  Rename…',
                                 command=lambda: do_rename(display, g))
                menu.add_command(label='  Hide from list',
                                 command=lambda: do_hide(display, g))
                menu.add_separator()
                menu.add_command(
                    label='  Merge into…',
                    command=lambda: do_merge(
                        display, g,
                        {k: rows[k].get('group') for k in rows if k != display},
                    ),
                )
                try:
                    menu.tk_popup(event.x_root, event.y_root)
                finally:
                    menu.grab_release()
            w.bind('<Button-3>', popup)

        for w in (f, rank_lbl, icon_lbl, name_lbl, meta_lbl, time_lbl, pct_lbl,
                  bar_frame, bar_cv):
            bind_ctx(w)

        return r

    def set_row_bg(r, bg, active):
        r['frame'].configure(bg=bg)
        for k in ('rank', 'icon', 'name', 'meta', 'time', 'pct', 'bar_frame'):
            r[k].configure(bg=bg)
        r['name'].configure(fg='white' if active else TEXT)

    # ---- Footer ----
    tk.Frame(root, bg=BORDER, height=1).pack(fill=tk.X)
    footer = tk.Frame(root, bg=BG)
    footer.pack(fill=tk.X, padx=28, pady=(6, 10))
    tk.Label(footer, text='● LIVE', font=('Segoe UI', 8, 'bold'),
             bg=BG, fg=ACCENT_2).pack(side=tk.LEFT)
    tk.Label(footer, text='   Right-click an app to rename / hide / merge.  '
                          f'Data: {tracker.storage.data_file}',
             font=('Segoe UI', 8), bg=BG, fg=MUTED).pack(side=tk.LEFT)

    # ---- refresh loop ----
    def refresh():
        if not alive[0]:
            return
        try:
            data, current, paused = tracker.snapshot()
        except Exception as e:
            logging.error('snapshot failed: %s', e)
            data, current, paused = {}, None, False

        rng = range_mode[0]
        visible, total_secs, max_secs = build_visible_rows(
            data, rng, search_var.get())

        range_label = {'today': 'TIME TODAY',
                       'week':  'TIME THIS WEEK',
                       'lifetime': 'TOTAL LIFETIME'}[rng]
        total_lbl.configure(text=range_label)
        total_val.config(text=fmt_duration(total_secs) if total_secs else '0s')
        apps_val.config(text=str(len(visible)))
        top_val.config(text=visible[0][0] if visible else '—')

        if paused:
            pill_text.config(text='Paused — no time being recorded')
            pill_dot.config(fg=PAUSE_FG)
        elif current and current not in tracker.skip_procs:
            cur_entry = data.get(current, {})
            cur_display = (cur_entry.get('alias')
                           or resolve_display_name(current, cur_entry.get('exe')))
            pill_text.config(text=f'Now tracking: {cur_display}')
            pill_dot.config(fg=ACCENT_2)
        else:
            pill_text.config(text='Idle')
            pill_dot.config(fg=MUTED)
        paint_pause(paused)

        # Clean up rows whose group no longer appears
        visible_displays = {d for d, _ in visible}
        for old in list(rows.keys()):
            if old not in visible_displays:
                rows[old]['frame'].destroy()
                del rows[old]

        # Ensure a row per visible group
        for display, g in visible:
            if display not in rows:
                r = make_row(display, g)
                r['group'] = g
                rows[display] = r
            else:
                rows[display]['group'] = g

        new_order = [d for d, _ in visible]
        order_changed = new_order != last_order[0]
        current_display = None
        if current and current not in tracker.skip_procs:
            cur_info = data.get(current, {})
            current_display = (cur_info.get('alias')
                               or resolve_display_name(current, cur_info.get('exe')))

        for rank_i, (display, g) in enumerate(visible, 1):
            r = rows[display]
            r['rank'].config(text=f'{rank_i:02d}')
            r['time'].config(text=fmt_duration(g['display_seconds']))

            # meta line: launches + first seen
            bits = []
            if g['launches']:
                bits.append(f"{g['launches']} sessions")
            fs = fmt_date(g['first_seen'])
            if fs:
                bits.append(f'since {fs}')
            r['meta'].config(text='  ·  '.join(bits) if bits else '')

            frac = (g['display_seconds'] / max_secs) if max_secs > 0 else 0
            r['bar_cv'].coords(r['bar_id'], 0, 0, BAR_W * frac, BAR_H)
            pct = (g['display_seconds'] / total_secs * 100) if total_secs > 0 else 0
            r['pct'].config(text=f'{pct:.1f}%')

            is_active = (not paused) and (display == current_display)
            set_row_bg(r, CARD_HI if is_active else CARD, is_active)

            if order_changed:
                r['frame'].grid(row=rank_i, column=0, sticky='ew', pady=3)

        last_order[0] = new_order
        root.after(UI_REFRESH_MS, refresh)

    def on_close():
        alive[0] = False
        try:
            canvas.unbind_all('<MouseWheel>')
        except Exception:
            pass
        root.destroy()
    root.protocol('WM_DELETE_WINDOW', on_close)

    refresh()
    root.lift()
    root.focus_force()
    root.mainloop()


# ---------------------------------------------------------------------------
# Tray icon
# ---------------------------------------------------------------------------
def make_icon():
    sz = 64
    img = Image.new('RGBA', (sz, sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 61, 61], fill='#17112e', outline='#c084fc', width=3)
    cx, cy = 32, 32
    for h in range(12):
        a = math.radians(h * 30 - 90)
        r1, r2 = 22, 26
        d.line([cx + r1*math.cos(a), cy + r1*math.sin(a),
                cx + r2*math.cos(a), cy + r2*math.sin(a)],
               fill='#2a1f52', width=2)
    d.line([cx, cy, cx - 11, cy - 14], fill='#c084fc', width=3)
    d.line([cx, cy, cx + 13, cy - 9],  fill='#f472b6', width=2)
    d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill='#c084fc')
    return img


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    global _dwm
    _dwm = ctypes.windll.dwmapi

    storage = Storage()
    storage.ensure_dirs()
    logging.basicConfig(
        filename=str(storage.log_file),
        level=logging.WARNING,
        format='%(asctime)s %(levelname)s %(message)s',
    )
    storage.rotate_backups()

    set_exe_describer(_file_description)

    tracker = AppTracker(storage=storage, exe_resolver=resolve_exe)
    tracker.focus_provider = make_focus_provider(tracker.skip_procs)

    # make sure data is saved even on normal interpreter exit
    atexit.register(tracker.stop)

    threading.Thread(target=tracker.track_loop, daemon=True, name='tracker').start()

    def on_view(icon, item):
        threading.Thread(target=show_stats_window, args=(tracker,),
                         daemon=True).start()

    def on_toggle_pause(icon, item):
        tracker.toggle_pause()
        icon.update_menu()

    def on_exit(icon, item):
        tracker.stop()
        icon.stop()

    icon = pystray.Icon(
        name='LifetimeTracker',
        icon=make_icon(),
        title='Lifetime App Tracker',
        menu=pystray.Menu(
            pystray.MenuItem('View Stats', on_view, default=True),
            pystray.MenuItem(
                'Pause tracking',
                on_toggle_pause,
                checked=lambda item: tracker.paused,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Exit', on_exit),
        ),
    )

    # wire milestone notifications through pystray's toast support
    def notify(title, message):
        try:
            icon.notify(message, title)
        except Exception as e:
            logging.warning('icon.notify failed: %s', e)
    tracker.notifier = notify

    icon.run()


if __name__ == '__main__':
    main()
