# Teleprompter

A lightweight, invisible-to-screen-capture teleprompter overlay for Windows 11. Read your script while screen sharing or recording — no one will see it.

## How It Works

Uses the Win32 API `SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE)` to make the window completely invisible to all screen capture software (OBS, Zoom, Teams, Discord, etc.). The window is fully visible on your monitor but doesn't exist for capture APIs.

## Requirements

- **Windows 10 2004+** or **Windows 11**
- **Python 3.10+** (tested on 3.14)

## Quick Start

```bash
# Install dependency (only needed once)
pip install keyboard

# Run
py app.py
```

## Usage

1. **Paste** your markdown script in the editor
2. Click **▶ Start Prompting** (or press `Ctrl+Enter`)
3. **Scroll manually** with mouse wheel, or enable auto-scroll
4. Use `Ctrl+Shift+Space` to toggle click-through mode (interact with apps behind the overlay)

## Global Hotkeys

| Shortcut | Action |
|---|---|
| `Ctrl+Shift+Space` | Toggle click-through / focus |
| `Ctrl+Shift+S` | Toggle auto-scroll |
| `Ctrl+Shift+Up` | Increase scroll speed |
| `Ctrl+Shift+Down` | Decrease scroll speed |
| `Ctrl+Shift+=` | Increase font size |
| `Ctrl+Shift+-` | Decrease font size |

## Markdown Support

Supports headings, **bold**, *italic*, `inline code`, fenced code blocks, blockquotes, ordered/unordered lists, horizontal rules, strikethrough, and links.

## Stealth

- **Single process** — just `python.exe` (or custom name if compiled)
- **No browser engine** — pure tkinter, no Electron/Chromium
- **Hidden from Alt+Tab** — uses `WS_EX_TOOLWINDOW` style
- **Invisible to capture** — `WDA_EXCLUDEFROMCAPTURE`

### Compile to standalone .exe (optional)

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name WinSvcHelper app.py
```

This produces a single `WinSvcHelper.exe` with no visible console window.
