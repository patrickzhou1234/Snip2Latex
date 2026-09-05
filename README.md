# Snip2Latex

Drag a box around anything on screen and get it back as LaTeX on your clipboard.

Hold <kbd>Win</kbd> and drag over a chunk of a PDF, a textbook photo, a whiteboard, a
handwritten worksheet — whatever. The region is sent to Gemini, transcribed to LaTeX, and
placed on your clipboard. A small banner tells you when it's working and when it's done, so
you know exactly when it's safe to paste. Nothing is left behind on your screen.

Built on [Snipper](https://www.autohotkey.com/boards/viewtopic.php?f=6&t=12088) by Fanatic Guru,
with an AI transcription pipeline layered on top.

---

## Requirements

|                                             |                                                                   |
| ------------------------------------------- | ----------------------------------------------------------------- |
| Windows                                     | 10 / 11                                                           |
| [AutoHotkey v2](https://www.autohotkey.com/) | v2.0 or later                                                     |
| Python                                      | 3.9+, on your`PATH` as `python.exe`                           |
| `google-genai`                            | `pip install google-genai`                                      |
| Gemini API key                              | free from[aistudio.google.com](https://aistudio.google.com/apikey) |

## Setup

**1. Install the Python dependency**

```powershell
pip install google-genai
```

**2. Set your API key**

`gemini.py` reads the key from the `GEMINI_API_KEY` environment variable. Set it once, for good:

```powershell
setx GEMINI_API_KEY "your-key-here"
```

Then open a **new** terminal (or log out and back in) so the variable is actually visible —
`setx` doesn't affect shells that are already running.

> Don't paste your key directly into `gemini.py`. It's a tracked file, so the key ends up in
> git history, and you can't get it back out again without rewriting history.

**3. Run it**

Double-click **`Snipper.ahk`**. A scissors icon appears in your system tray — that's it, it's
listening.

> ⚠️ `Snipper.exe` is a stale compiled build and does **not** include the AI pipeline. Run the
> `.ahk` directly, or recompile it with Ahk2Exe if you want a single-file version.

To start it automatically with Windows, press <kbd>Win</kbd>+<kbd>R</kbd>, run `shell:startup`,
and drop a shortcut to `Snipper.ahk` in the folder that opens.

---

## Usage

| Hotkey                                  | What it does                                                            |
| --------------------------------------- | ----------------------------------------------------------------------- |
| <kbd>Win</kbd> + drag                   | **AI snip** — transcribe the region to LaTeX and copy it         |
| <kbd>Win</kbd>+<kbd>Ctrl</kbd> + drag   | Plain snip — leaves a floating image on screen*and* copies the image |
| <kbd>Win</kbd>+<kbd>Alt</kbd> + drag    | Copy the region to the clipboard as an image, nothing else              |
| <kbd>Shift</kbd>+<kbd>PrintScreen</kbd> | Show / hide all floating snips                                          |

The usual flow is: <kbd>Win</kbd>+drag, wait for the green banner, then <kbd>Ctrl</kbd>+<kbd>V</kbd>
into your editor.

### The indicator

A small banner appears just under the region you selected. It never takes focus and clicks pass
straight through it, so it can't get in your way.

|                                       |                                         |
| ------------------------------------- | --------------------------------------- |
| 🟠`Reading snip...`                 | request in flight                       |
| 🟢`Copied to clipboard - 412 chars` | done, safe to paste (hides after ~1.5s) |
| 🔴`Failed - <reason>`               | something went wrong (hides after ~6s)  |

You'll always get one of the last two. It never just silently stops.

Snipping again while a request is still running cancels the old one and starts fresh, so you're
never left waiting on a stale result.

### Precise selections

Both plain-snip hotkeys support the original Snipper selection tools:

- Keep <kbd>Shift</kbd> held **as you release** the mouse to enter adjust mode, drag the edges to
  fine-tune, then press <kbd>Enter</kbd> to confirm.
- In adjust mode, right-click the `W x H` readout to type in exact dimensions or lock the aspect
  ratio.

### Floating snips

The snips left by <kbd>Win</kbd>+<kbd>Ctrl</kbd>+drag stay pinned on top of every window. Drag
them anywhere, right-click one for a menu (copy, save to file, settings), or press
<kbd>Esc</kbd> while one is focused to close it.

---

## Configuration

Near the top of **`Snipper.ahk`**:

```ahk
AI_Python := 'python.exe'   ; use a full path if python isn't on your PATH
AI_Timeout := 90000         ; ms to wait for gemini.py before giving up
```

Set `AI_Python` to something like `'C:\Users\you\venv\Scripts\python.exe'` if you keep the
`google-genai` install in a virtualenv.

In **`gemini.py`**:

```python
MODEL = "gemini-flash-latest"   # swap for a heavier model if you want
PROMPT = (...)                  # what you're asking the model to do
```

`PROMPT` is where you change the output format. It currently asks for bare LaTeX with no
preamble and no commentary. An alternate prompt that also transcribes the question number is
sitting commented out just above it. If you'd rather have plain text, Markdown, or a solved
answer instead of a transcription, this one string is the only thing you need to edit.

---

## How it works

```
Win+drag  →  image.png  →  gemini.py  →  response.txt  →  clipboard
                              ↓
                        response.done      ("OK" or "ERR ...")
```

`Snipper.ahk` captures the region straight to `image.png` and launches `gemini.py` hidden. It
then polls for **`response.done`** — a marker file that `gemini.py` writes last, atomically, and
writes *unconditionally*, whether the request succeeded or blew up.

That marker is what makes the whole thing dependable. Watching `response.txt` for changes
instead (the obvious approach) breaks in three ways: you can read the file mid-write and paste
something truncated; an answer identical to the previous one looks like nothing happened; and a
crashed `gemini.py` never changes anything, so you wait forever. Waiting on a
written-last-written-always marker sidesteps all three.

On top of that, the script gives up if `gemini.py` exits without producing a marker, times out
and kills the process after `AI_Timeout`, and reads the clipboard back after writing to confirm
the paste will actually contain your transcription. `gemini.py` retries the transient `429` and
`503` responses that the API hands out under load.

### Files in this folder

| File              |                                                          |
| ----------------- | -------------------------------------------------------- |
| `Snipper.ahk`   | the whole thing — hotkeys, capture, indicator, pipeline |
| `gemini.py`     | sends the image to Gemini, writes the result             |
| `image.png`     | your most recent capture (overwritten every snip)        |
| `response.txt`  | your most recent transcription                           |
| `response.done` | status marker;`OK`, or `ERR <type>: <message>`       |
| `Snipper.exe`   | stale compiled build, no AI pipeline — ignore it        |

When something fails, `response.done` has the full error in it. The banner truncates long
messages; that file doesn't.

---

## Troubleshooting

**`Failed - Cannot start python.exe`**
Python isn't on your `PATH`. Point `AI_Python` at the full path to your interpreter.

**`Failed - gemini.py exited without a result`**
`gemini.py` died on startup — almost always a missing package. Run it by hand to see the real
error:

```powershell
python gemini.py
type response.done
```

**`Failed - ERR ClientError: 400 ... API key not valid`**
`GEMINI_API_KEY` isn't set, or the script was started before you set it. Set it, then restart
`Snipper.ahk` — it inherits the environment from whenever it launched.

**`Failed - Timed out after 90s`**
The request hung. Just snip again; if it keeps happening, check your connection or raise
`AI_Timeout`.

**Nothing happens at all**
Check that the scissors icon is in your tray. If another AutoHotkey script has already claimed
<kbd>Win</kbd>+click, one of them wins and it may not be this one.

**The transcription is wrong or partial**
Snip tighter around the content and avoid catching page edges or margins. Blurry photos of
handwriting are the hardest case — the model does noticeably better on a larger, sharper crop.
