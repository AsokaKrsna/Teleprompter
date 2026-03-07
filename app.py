# -*- coding: utf-8 -*-
"""
Teleprompter - Screen-Capture Invisible Overlay
Global Hotkeys:
  Ctrl+Shift+Space  Toggle click-through
  Ctrl+Shift+S      Toggle auto-scroll
  Ctrl+Shift+Up     Faster scroll
  Ctrl+Shift+Down   Slower scroll
  Ctrl+Shift+=      Bigger font
  Ctrl+Shift+-      Smaller font
"""

import ctypes
import ctypes.wintypes
import tkinter as tk
import re
import threading
import sys

# ---- Win32 ----
WDA_EXCLUDEFROMCAPTURE = 0x00000011
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000
LWA_ALPHA = 0x02
WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000
VK_SPACE = 0x20
VK_S = 0x53
VK_UP = 0x26
VK_DOWN = 0x28
VK_OEM_PLUS = 0xBB
VK_OEM_MINUS = 0xBD
SW_MINIMIZE = 6
SW_RESTORE = 9
SW_SHOW = 5

user32 = ctypes.windll.user32
user32.SetWindowLongW.argtypes = [ctypes.wintypes.HWND, ctypes.c_int, ctypes.c_long]
user32.SetWindowLongW.restype = ctypes.c_long
user32.GetWindowLongW.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
user32.GetWindowLongW.restype = ctypes.c_long
user32.SetLayeredWindowAttributes.argtypes = [
    ctypes.wintypes.HWND, ctypes.wintypes.COLORREF, ctypes.wintypes.BYTE, ctypes.wintypes.DWORD
]
user32.SetWindowDisplayAffinity.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.DWORD]
user32.SetWindowDisplayAffinity.restype = ctypes.wintypes.BOOL
user32.RegisterHotKey.argtypes = [ctypes.wintypes.HWND, ctypes.c_int, ctypes.wintypes.UINT, ctypes.wintypes.UINT]
user32.RegisterHotKey.restype = ctypes.wintypes.BOOL
user32.UnregisterHotKey.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
user32.GetMessageW.argtypes = [ctypes.POINTER(ctypes.wintypes.MSG), ctypes.wintypes.HWND,
                                ctypes.wintypes.UINT, ctypes.wintypes.UINT]
user32.GetMessageW.restype = ctypes.wintypes.BOOL
user32.PostThreadMessageW.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.UINT,
                                       ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM]
user32.ShowWindow.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = ctypes.wintypes.BOOL

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass

# ---- Theme (screen-background-aware, optimized for transparency) ----
TXT = '#ffffff'  # pure white for ALL text (bold/italic/normal)
C = {
    'bg': '#0a0e1a', 'bg2': '#0d1220', 'surface': '#131828',
    'hover': '#1a2038', 'border': '#283050',
    'text': TXT, 'dim': TXT, 'muted': TXT,
    'accent': '#6e8efb', 'accent2': '#8aa4ff',
    'green': '#34d399', 'red': '#f87171', 'yellow': '#fbbf24',
    'code_bg': '#0c1018', 'quote_bg': '#0e1225',
}


class MarkdownRenderer:
    def __init__(self, text_widget):
        self.w = text_widget
        self._setup(16)

    def _setup(self, sz):
        w = self.w
        # All text uses the SAME foreground color — only weight/style differs
        w.tag_configure('h1', font=('Segoe UI', sz + 12, 'bold'), foreground=TXT,
                        spacing1=14, spacing3=8, lmargin1=4, lmargin2=4)
        w.tag_configure('h2', font=('Segoe UI', sz + 8, 'bold'), foreground=TXT,
                        spacing1=12, spacing3=6, lmargin1=4, lmargin2=4)
        w.tag_configure('h3', font=('Segoe UI', sz + 4, 'bold'), foreground=TXT,
                        spacing1=10, spacing3=5, lmargin1=4, lmargin2=4)
        w.tag_configure('h4', font=('Segoe UI', sz + 2, 'bold'), foreground=TXT,
                        spacing1=8, spacing3=4, lmargin1=4, lmargin2=4)
        w.tag_configure('p', font=('Segoe UI', sz), foreground=TXT,
                        spacing1=3, spacing3=3, lmargin1=4, lmargin2=4, wrap='word')
        w.tag_configure('bold', font=('Segoe UI', sz, 'bold'), foreground=TXT)
        w.tag_configure('italic', font=('Segoe UI', sz, 'italic'), foreground=TXT)
        w.tag_configure('bold_italic', font=('Segoe UI', sz, 'bold italic'), foreground=TXT)
        w.tag_configure('code', font=('Cascadia Code', max(10, sz - 2)), foreground=TXT,
                        background=C['code_bg'])
        w.tag_configure('code_block', font=('Cascadia Code', max(10, sz - 2)), foreground=TXT,
                        background=C['code_bg'], spacing1=6, spacing3=6,
                        lmargin1=16, lmargin2=16, rmargin=16, wrap='word')
        w.tag_configure('quote', font=('Segoe UI', sz, 'italic'), foreground=C['dim'],
                        background=C['quote_bg'], spacing1=4, spacing3=4, lmargin1=20, lmargin2=20)
        w.tag_configure('hr', font=('Segoe UI', 2), foreground=C['border'],
                        spacing1=10, spacing3=10, justify='center')
        w.tag_configure('li', font=('Segoe UI', sz), foreground=TXT,
                        lmargin1=20, lmargin2=36, spacing1=2, spacing3=2, wrap='word')
        w.tag_configure('bullet', foreground=C['accent'], font=('Segoe UI', sz))
        w.tag_configure('num', foreground=C['accent'], font=('Segoe UI', sz, 'bold'))
        w.tag_configure('strike', font=('Segoe UI', sz), overstrike=True, foreground=C['dim'])
        w.tag_configure('link', foreground=C['accent'], underline=True, font=('Segoe UI', sz))

    def set_size(self, sz):
        self._setup(sz)

    def render(self, md):
        self.w.configure(state='normal')
        self.w.delete('1.0', 'end')
        lines = md.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            stripped = line.strip()

            # fenced code block
            if stripped.startswith('```'):
                code = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code.append(lines[i])
                    i += 1
                if i < len(lines):
                    i += 1
                self.w.insert('end', '\n'.join(code) + '\n', 'code_block')
                continue

            # horizontal rule
            if stripped and re.fullmatch(r'[-*_]{3,}', stripped):
                self.w.insert('end', '\u2500' * 50 + '\n', 'hr')
                i += 1
                continue

            # heading
            m = re.match(r'^(#{1,4})\s+(.*)', line)
            if m:
                self._inline(m.group(2).strip(), 'h' + str(min(len(m.group(1)), 4)))
                self.w.insert('end', '\n')
                i += 1
                continue

            # blockquote
            if stripped.startswith('>'):
                self.w.insert('end', '  \u2502 ', 'quote')
                self._inline(re.sub(r'^>\s*', '', stripped), 'quote')
                self.w.insert('end', '\n')
                i += 1
                continue

            # unordered list
            m = re.match(r'^(\s*)[-*+]\s+(.*)', line)
            if m:
                self.w.insert('end', '  ' * (len(m.group(1)) // 2) + '\u2022 ', 'bullet')
                self._inline(m.group(2), 'li')
                self.w.insert('end', '\n')
                i += 1
                continue

            # ordered list
            m = re.match(r'^(\s*)(\d+)\.\s+(.*)', line)
            if m:
                self.w.insert('end', '  ' * (len(m.group(1)) // 2) + m.group(2) + '. ', 'num')
                self._inline(m.group(3), 'li')
                self.w.insert('end', '\n')
                i += 1
                continue

            # blank
            if not stripped:
                self.w.insert('end', '\n')
                i += 1
                continue

            # paragraph
            self._inline(line, 'p')
            self.w.insert('end', '\n')
            i += 1
        self.w.configure(state='disabled')

    def _inline(self, text, tag):
        pat = re.compile(
            r'\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*'
            r'|`([^`]+)`|~~(.+?)~~|\[([^\]]+)\]\([^)]+\)'
        )
        pos = 0
        for m in pat.finditer(text):
            if m.start() > pos:
                self.w.insert('end', text[pos:m.start()], tag)
            if m.group(1):   self.w.insert('end', m.group(1), 'bold_italic')
            elif m.group(2): self.w.insert('end', m.group(2), 'bold')
            elif m.group(3): self.w.insert('end', m.group(3), 'italic')
            elif m.group(4): self.w.insert('end', ' ' + m.group(4) + ' ', 'code')
            elif m.group(5): self.w.insert('end', m.group(5), 'strike')
            elif m.group(6): self.w.insert('end', m.group(6), 'link')
            pos = m.end()
        if pos < len(text):
            self.w.insert('end', text[pos:], tag)


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Teleprompter')
        self.root.configure(bg=C['bg'])
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)

        sw = self.root.winfo_screenwidth()
        w, h = 700, 460
        x = (sw - w) // 2
        self.root.geometry(f'{w}x{h}+{x}+30')
        self.root.minsize(350, 220)

        self.auto_scroll = False
        self.speed = 3
        self.font_size = 16
        self.opacity = 0.55
        self.click_through = False
        self.prompting = False
        self.minimized = False
        self.hotkey_thread_id = None
        self.ctrl_held = False
        self._drag = {'x': 0, 'y': 0}
        self._rsz = {'x': 0, 'y': 0, 'w': 0, 'h': 0}

        self._build_titlebar()
        self._build_edit()
        self.edit_frame.pack(fill='both', expand=True)
        self.root.after(50, lambda: self.grip.lift())
        self.root.after(300, self._apply_win32)
        self.root.after(150, self._poll_ctrl)

    # ---- Win32 ----
    def _get_hwnd(self):
        return int(self.root.wm_frame(), 16)

    def _apply_win32(self):
        try:
            hwnd = self._get_hwnd()
            r = user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            print(f'[+] Capture protection: {"ACTIVE" if r else "FAILED"}', flush=True)
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style |= WS_EX_TOOLWINDOW
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            self._set_opacity(self.opacity)
        except Exception as e:
            print(f'[!] Win32 error: {e}', flush=True)
        threading.Thread(target=self._hotkey_thread, daemon=True).start()

    def _set_opacity(self, val):
        self.opacity = max(0.15, min(1.0, val))
        try:
            hwnd = self._get_hwnd()
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style |= WS_EX_LAYERED
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            user32.SetLayeredWindowAttributes(hwnd, 0, int(self.opacity * 255), LWA_ALPHA)
            user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        except Exception:
            pass

    def _poll_ctrl(self):
        if self.prompting:
            # VK_CONTROL is 0x11, VK_MENU (Alt) is 0x12
            ctrl = (user32.GetAsyncKeyState(0x11) & 0x8000) != 0
            alt = (user32.GetAsyncKeyState(0x12) & 0x8000) != 0
            is_held = ctrl and alt
            if is_held != self.ctrl_held:
                self.ctrl_held = is_held
                self._apply_click_through_state()
        self.root.after(150, self._poll_ctrl)

    def _apply_click_through_state(self):
        try:
            hwnd = self._get_hwnd()
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            if not self.prompting or self.ctrl_held:
                # Make clickable (remove TRANSPARENT)
                style &= ~WS_EX_TRANSPARENT
                user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
                self._set_opacity(self.opacity)
                if self.prompting:
                    self.status_lbl.configure(text='LIVE (Hold Ctrl+Alt to Click)', fg=C['green'])
                else:
                    self.status_lbl.configure(text='EDIT', fg=C['accent'])
            else:
                # Make pass-through (add TRANSPARENT)
                style |= WS_EX_TRANSPARENT | WS_EX_LAYERED
                user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
                self._set_opacity(self.opacity)
                if self.prompting:
                    self.status_lbl.configure(text='LIVE (Pass-through)', fg='white')
            user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        except Exception:
            pass

    def _minimize(self):
        """Minimize using Win32 ShowWindow (works with frameless windows)."""
        try:
            hwnd = self._get_hwnd()
            user32.ShowWindow(hwnd, SW_MINIMIZE)
            self.minimized = True
        except Exception:
            pass

    def _restore(self):
        """Restore from minimize."""
        try:
            hwnd = self._get_hwnd()
            user32.ShowWindow(hwnd, SW_RESTORE)
            self.root.attributes('-topmost', True)
            self._set_opacity(self.opacity)
            user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            self.minimized = False
        except Exception:
            pass

    # ---- Hotkeys (Win32 RegisterHotKey) ----
    def _hotkey_thread(self):
        self.hotkey_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        mods = MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT
        keys = [(2, VK_S), (3, VK_UP), (4, VK_DOWN), (5, VK_OEM_PLUS), (6, VK_OEM_MINUS)]
        ok = sum(1 for hid, vk in keys if user32.RegisterHotKey(None, hid, mods, vk))
        print(f'[+] Global hotkeys: {ok}/{len(keys)} registered', flush=True)

        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY:
                hid = msg.wParam
                actions = {
                    2: self._toggle_auto_scroll,
                    3: lambda: self._adj_speed(1),
                    4: lambda: self._adj_speed(-1),
                    5: lambda: self._adj_font(2),
                    6: lambda: self._adj_font(-2),
                }
                fn = actions.get(hid)
                if fn:
                    self.root.after(0, fn)

    # ---- Title bar ----
    def _build_titlebar(self):
        tb = tk.Frame(self.root, bg=C['bg2'], height=32, cursor='fleur')
        tb.pack(fill='x', side='top')
        tb.pack_propagate(False)

        tb.bind('<Button-1>', self._drag_start)
        tb.bind('<B1-Motion>', self._drag_move)
        # double-click titlebar to restore from minimized if needed
        tb.bind('<Double-Button-1>', lambda e: self._restore() if self.minimized else None)

        for col in [C['red'], C['yellow'], C['green']]:
            c = tk.Canvas(tb, width=9, height=9, bg=C['bg2'], highlightthickness=0)
            c.create_oval(1, 1, 8, 8, fill=col, outline='')
            c.pack(side='left', padx=(6 if col == C['red'] else 2, 0), pady=11)
            c.bind('<Button-1>', self._drag_start)
            c.bind('<B1-Motion>', self._drag_move)

        self.status_lbl = tk.Label(tb, text='EDIT', bg=C['bg2'], fg=C['accent'],
                                    font=('Segoe UI', 8, 'bold'), padx=8)
        self.status_lbl.pack(side='left')
        self.status_lbl.bind('<Button-1>', self._drag_start)
        self.status_lbl.bind('<B1-Motion>', self._drag_move)

        # Close (right-most)
        tk.Button(tb, text='\u00D7', bg=C['bg2'], fg=C['dim'], font=('Segoe UI', 12),
                  bd=0, padx=6, activebackground=C['red'], activeforeground='white',
                  highlightthickness=0, cursor='hand2', command=self._quit
                  ).pack(side='right', padx=(0, 4))

        # Minimize
        tk.Button(tb, text='\u2013', bg=C['bg2'], fg=C['dim'], font=('Segoe UI', 10),
                  bd=0, padx=6, activebackground=C['hover'], activeforeground='white',
                  highlightthickness=0, cursor='hand2', command=self._minimize
                  ).pack(side='right')

        # Resize grip on root
        self.grip = tk.Label(self.root, text=' // ', bg=C['bg2'], fg=C['muted'],
                              font=('Consolas', 8), cursor='size_nw_se')
        self.grip.place(relx=1.0, rely=1.0, anchor='se')
        self.grip.bind('<Button-1>', self._resize_start)
        self.grip.bind('<B1-Motion>', self._resize_move)

    # ---- Edit mode ----
    def _build_edit(self):
        self.edit_frame = tk.Frame(self.root, bg=C['bg'])

        bar = tk.Frame(self.edit_frame, bg=C['bg2'])
        bar.pack(side='bottom', fill='x', padx=0, pady=0)

        tk.Label(bar, text=' Ctrl+Enter = Start  |  Hold Ctrl+Alt to interact while LIVE',
                 bg=C['bg2'], fg=C['muted'], font=('Segoe UI', 8)).pack(side='left', padx=8, pady=8)

        tk.Button(bar, text='  \u25B6  Start Prompting  ', bg=C['accent'], fg='white',
                  font=('Segoe UI', 11, 'bold'), bd=0, padx=18, pady=6,
                  activebackground=C['accent2'], activeforeground='white',
                  highlightthickness=0, cursor='hand2',
                  command=self._start_prompting).pack(side='right', padx=8, pady=6)

        # THEN the textarea fills remaining space
        self.inp = tk.Text(self.edit_frame, bg=C['surface'], fg=C['text'],
                           font=('Cascadia Code', 11), insertbackground=C['accent'],
                           selectbackground=C['accent'], selectforeground='white',
                           wrap='word', relief='flat', bd=0, padx=12, pady=10, undo=True)
        self.inp.pack(fill='both', expand=True, padx=8, pady=(4, 0))
        self.inp.insert('1.0', '# Paste your script here\n\nSupports **markdown** formatting.')

    # ---- Prompter mode ----
    def _build_prompter(self):
        self.pframe = tk.Frame(self.root, bg=C['bg'])

        # CONTROLS BAR AT BOTTOM FIRST so it never clips
        ctrl = tk.Frame(self.pframe, bg=C['bg2'])
        ctrl.pack(side='bottom', fill='x')

        lf = tk.Frame(ctrl, bg=C['bg2'])
        lf.pack(side='left', padx=6, pady=5)
        self._cbtn(lf, '\u25C0 Edit', self._stop_prompting)
        self._sep(lf)
        self.scroll_btn = self._cbtn(lf, '\u25B6 Scroll', self._toggle_auto_scroll)
        self._cbtn(lf, ' - ', lambda: self._adj_speed(-1))
        self.speed_lbl = tk.Label(lf, text='3', bg=C['bg2'], fg=C['dim'],
                                   font=('Cascadia Code', 9), width=2)
        self.speed_lbl.pack(side='left')
        self._cbtn(lf, ' + ', lambda: self._adj_speed(1))

        rf = tk.Frame(ctrl, bg=C['bg2'])
        rf.pack(side='right', padx=(6, 28), pady=5)  # extra right pad to clear resize grip
        tk.Label(rf, text='Font', bg=C['bg2'], fg=C['muted'], font=('Segoe UI', 8)).pack(side='left', padx=2)
        self._cbtn(rf, '-', lambda: self._adj_font(-2))
        self.font_lbl = tk.Label(rf, text='16', bg=C['bg2'], fg=C['dim'],
                                  font=('Cascadia Code', 9), width=3)
        self.font_lbl.pack(side='left')
        self._cbtn(rf, '+', lambda: self._adj_font(2))
        self._sep(rf)
        tk.Label(rf, text='Opacity', bg=C['bg2'], fg=C['muted'], font=('Segoe UI', 8)).pack(side='left', padx=2)
        self._cbtn(rf, '-', lambda: self._adj_opacity(-10))
        self.opacity_lbl = tk.Label(rf, text=f'{int(self.opacity*100)}%', bg=C['bg2'], fg=C['dim'],
                                     font=('Cascadia Code', 9), width=4)
        self.opacity_lbl.pack(side='left')
        self._cbtn(rf, '+', lambda: self._adj_opacity(10))

        # PROGRESS BAR
        pf = tk.Frame(self.pframe, bg=C['bg2'], height=2)
        pf.pack(side='bottom', fill='x')
        pf.pack_propagate(False)
        self.prog = tk.Frame(pf, bg=C['accent'], height=2)
        self.prog.place(x=0, y=0, relheight=1, relwidth=0)

        # TEXT fills remaining space
        self.ptext = tk.Text(self.pframe, bg=C['bg'], fg=C['text'], font=('Segoe UI', 14),
                              wrap='word', relief='flat', bd=0, padx=20, pady=14,
                              cursor='arrow', state='disabled', spacing1=1, spacing3=1)
        self.ptext.pack(fill='both', expand=True)
        self.ptext.bind('<MouseWheel>', self._on_wheel)

        self.renderer = MarkdownRenderer(self.ptext)

    def _cbtn(self, parent, txt, cmd):
        b = tk.Button(parent, text=txt, bg=C['surface'], fg=C['dim'],
                       font=('Segoe UI', 9), bd=0, padx=6, pady=1,
                       activebackground=C['hover'], activeforeground=C['text'],
                       highlightthickness=0, cursor='hand2', command=cmd)
        b.pack(side='left', padx=1)
        return b

    def _sep(self, parent):
        tk.Frame(parent, bg=C['border'], width=1, height=16).pack(side='left', padx=4)

    # ---- Mode switching ----
    def _start_prompting(self):
        try:
            script = self.inp.get('1.0', 'end-1c').strip()
            if not script:
                return
            self.renderer.set_size(self.font_size)
            self.renderer.render(script)
            self.edit_frame.pack_forget()
            self.pframe.pack(fill='both', expand=True)
            self.prompting = True
            
            # Immediately evaluate Ctrl+Alt state on entry
            self.ctrl_held = ((user32.GetAsyncKeyState(0x11) & 0x8000) != 0) and ((user32.GetAsyncKeyState(0x12) & 0x8000) != 0)
            self._apply_click_through_state()
            
            self.ptext.yview_moveto(0)
            self.grip.lift()
        except Exception as e:
            print(f'[!] Start error: {e}', flush=True)

    def _stop_prompting(self):
        if self.auto_scroll:
            self._toggle_auto_scroll()
        self.pframe.pack_forget()
        self.edit_frame.pack(fill='both', expand=True)
        self.prompting = False
        self._apply_click_through_state()
        self.grip.lift()

    # ---- Scroll ----
    def _toggle_auto_scroll(self):
        self.auto_scroll = not self.auto_scroll
        if self.auto_scroll:
            self.scroll_btn.configure(bg=C['accent'], fg='white')
            self._scroll_tick()
        else:
            self.scroll_btn.configure(bg=C['surface'], fg=C['dim'])

    def _scroll_tick(self):
        if not self.auto_scroll or not self.prompting:
            return
        cur = self.ptext.yview()
        if cur[1] < 1.0:
            step = (0.15 + self.speed * 0.35) / max(1, self.ptext.winfo_height() * 8)
            self.ptext.yview_moveto(cur[0] + step)
            self._update_prog()
            self.root.after(max(16, 55 - self.speed * 4), self._scroll_tick)
        else:
            self._toggle_auto_scroll()

    def _adj_speed(self, d):
        self.speed = max(1, min(10, self.speed + d))
        self.speed_lbl.configure(text=str(self.speed))

    def _on_wheel(self, e):
        self.ptext.yview_scroll(-1 * (e.delta // 120), 'units')
        self._update_prog()

    def _update_prog(self):
        try:
            self.prog.place(x=0, y=0, relheight=1, relwidth=min(1.0, self.ptext.yview()[1]))
        except Exception:
            pass

    # ---- Font ----
    def _adj_font(self, d):
        self.font_size = max(10, min(42, self.font_size + d))
        self.font_lbl.configure(text=str(self.font_size))
        if self.prompting:
            self.renderer.set_size(self.font_size)

    # ---- Opacity ----
    def _adj_opacity(self, delta):
        new_val = max(15, min(100, int(self.opacity * 100) + delta))
        self._set_opacity(new_val / 100)
        self.opacity_lbl.configure(text=f'{new_val}%')

    # ---- Status flash ----
    def _flash(self, txt):
        self.status_lbl.configure(text=txt, fg=C['accent2'])
        self.root.after(2500, lambda: self.status_lbl.configure(
            text='LIVE' if self.prompting else 'EDIT',
            fg=C['green'] if self.prompting else C['accent']))

    # ---- Drag ----
    def _drag_start(self, e):
        self._drag = {'x': e.x_root - self.root.winfo_x(), 'y': e.y_root - self.root.winfo_y()}

    def _drag_move(self, e):
        self.root.geometry(f'+{e.x_root - self._drag["x"]}+{e.y_root - self._drag["y"]}')

    # ---- Resize ----
    def _resize_start(self, e):
        self._rsz = {'x': e.x_root, 'y': e.y_root,
                      'w': self.root.winfo_width(), 'h': self.root.winfo_height()}

    def _resize_move(self, e):
        nw = max(350, self._rsz['w'] + e.x_root - self._rsz['x'])
        nh = max(220, self._rsz['h'] + e.y_root - self._rsz['y'])
        self.root.geometry(f'{nw}x{nh}')

    # ---- Quit ----
    def _quit(self):
        if self.hotkey_thread_id:
            for i in range(1, 7):
                user32.UnregisterHotKey(None, i)
            try:
                user32.PostThreadMessageW(self.hotkey_thread_id, 0x0012, 0, 0)
            except Exception:
                pass
        self.root.destroy()
        sys.exit(0)

    def run(self):
        self.root.bind('<Escape>', lambda e: self._stop_prompting() if self.prompting else None)
        self.root.bind('<Control-Return>', lambda e: self._start_prompting())
        self.root.mainloop()


if __name__ == '__main__':
    App().run()
