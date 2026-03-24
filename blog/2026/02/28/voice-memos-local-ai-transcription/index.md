# From Voice Memos to Searchable Text with Local Whisper on macOS

**Date:** February 28, 2026  
**Author:** Eugene Petrenko  
**Tags:** LocalAI, python, macos, whisper, ai-coding, automation, apple-silicon, voice-memos

---

I record voice memos constantly -- ideas during walks, meeting notes, random thoughts at 2 AM.
The macOS and mainly watchOS Voice Memos app is perfect for capture, but terrible for retrieval. You can't search
recordings. You can't grep audio. Those ideas just sit there, locked in `.m4a` files, slowly
becoming irrelevant.

The obvious solution is transcription. Cloud services like Otter.ai or Whisper API do this
well -- but they cost money, require internet, and send your private voice recordings to someone
else's servers. For notes about work projects, product ideas, and personal reflections, that's
a non-starter.

So I built a pipeline that runs **entirely on a MacBook**. It pulls recordings from Voice Memos
via AppleScript, transcribes them with [Whisper][whisper] running locally on Apple Silicon, and
outputs searchable markdown files. No cloud. No API keys. No subscriptions.

> **Want to skip the explanation and just run it?** The "Putting It All Together" section has
> a complete, copy-paste-and-`uv run` script. The production version with state management
> and CLI options lives in my internal repository.

---

## Why LocaAI Transcription Matters

Before diving into the code, here's why this matters beyond privacy:

- **No recurring cost.** Cloud transcription services charge per minute of audio. A 30-minute
  daily voice memo habit costs $15--50/month. Local inference costs electricity.
- **Works offline.** On planes, in tunnels, in countries with restricted internet -- your
  transcription pipeline doesn't care.
- **No data leaves your machine.** Voice memos often contain sensitive content: product ideas,
  performance reviews, personal reflections. Local processing keeps it local.
- **Unlimited volume.** No API rate limits, no monthly quotas. Transcribe your entire archive
  overnight.

The catch? You need an Apple Silicon Mac with enough RAM, and the first-time model download is
~1.6 GB. After that, everything runs locally.

---

## System Requirements

Here's what you need to run this pipeline. I've tested it on an M1 MacBook Air (16 GB) and an
M4 Max MacBook Pro (128 GB):

| Component            | Requirement                                         |
|----------------------|-----------------------------------------------------|
| **Mac**              | Apple Silicon (M1, M2, M3, M4 -- any variant)       |
| **RAM**              | 16 GB, 32 GB+ recommended                           |
| **Disk**             | ~1.6 GB for the model + ~1 MB per hour of recordings |
| **macOS**            | Sequoia 15.x (tested); Sonoma 14.x likely works     |
| **Python**           | 3.11+                                               |
| **uv**              | Latest ([astral.sh/uv][uv-install])                 |
| **ffmpeg**           | Required by mlx-whisper (`brew install ffmpeg`)     |
| **Accessibility**    | Terminal must have Accessibility permission         |

The Whisper large-v3-turbo model runs comfortably on an M1 with 16 GB. On an M4 Max, it
transcribes roughly 10x faster than real-time -- a 10-minute memo in about 60 seconds. On a
base M1, expect roughly 1x real-time (1 minute of audio takes ~1 minute of processing).

---

## The Architecture

The pipeline has two independent phases:

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Voice Memos    │     │  Export Audio    │     │  Transcribe      │
│  (macOS app)    │────▶│  (AppleScript    │────▶│  (mlx-whisper    │
│                 │     │   + clipboard)   │     │   or Ollama)     │
└─────────────────┘     └──────────────────┘     └──────────────────┘
                              │                         │
                              ▼                         ▼
                         .m4a files                .md transcripts
```

**Phase 1: Fetch** -- AppleScript reads the Voice Memos sidebar, selects each recording, copies
it via Cmd+C, and saves the M4A data from the clipboard to disk.

**Phase 2: Transcribe** -- A local Whisper model converts each audio file to text. Two backends
are supported: [mlx-whisper][mlx-whisper] (Apple Silicon native) and [Ollama][ollama] (more
flexible, supports NVIDIA GPUs too).

Both phases are fully incremental -- they skip recordings that have already been processed.

---

## The Problem with Voice Memos (and What I Tried First)

Here's the first challenge: **macOS Voice Memos has no API**. There's no AppleScript dictionary,
no command-line tool, no SQLite database you can query. Apple doesn't expose the recordings
through any documented interface.

My first attempt was to access the files directly. The recordings live under
`~/Library/Group Containers/group.com.apple.VoiceMemos.shared/`, in a CoreData/CloudKit-backed
structure. I wrote a script that found `.m4a` files in there and copied them out. It worked --
until iCloud sync kicked in.

My second attempt used `NSSharingService` through PyObjC to trigger the system share sheet. The
share sheet requires user interaction for each recording. For 20+ memos, that's 20+ clicks.

The approach that actually works is the most hacky one: **UI automation via the Accessibility
API**. It's ugly, it breaks when Apple changes the UI, and it requires your terminal to have
Accessibility permission. But it reliably exports audio without corrupting sync state.

### Before You Start

A quick checklist before running the scripts:

1. **Grant Accessibility permission.** System Settings > Privacy & Security > Accessibility --
   add your terminal app (Terminal.app, iTerm2, Warp, or whichever you use).
2. **Open Voice Memos** and select "All Recordings" in the sidebar.
3. **Install prerequisites:** `brew install ffmpeg` and
   [install uv](https://docs.astral.sh/uv/).
4. **Verify Accessibility works** with a test command:

```bash
osascript -e 'tell application "System Events" to get name of first process'
```

If this returns a process name, you're good. If it errors, check your Accessibility settings.

---

## Step 1: Listing Voice Memos

The first script reads the Voice Memos sidebar to discover all recordings. Voice Memos on macOS
Sequoia nests its sidebar buttons **13 groups deep** inside the window hierarchy. I discovered
this number through trial and error with Accessibility Inspector done by AI Agent.

```python
import subprocess


def run_applescript(script: str) -> str:
    """Run an AppleScript and return stdout."""
    proc = subprocess.run(
        ["osascript", "-"],
        input=script, text=True,
        capture_output=True, timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"osascript failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def list_voice_memos() -> list[dict]:
    # Voice Memos nests its sidebar 13 groups deep
    group_ref = "window 1"
    for _ in range(13):
        group_ref = f"group 1 of {group_ref}"

    script = f'''
tell application "VoiceMemos" to activate
delay 0.5
tell application "System Events"
    tell process "VoiceMemos"
        set theGroup to {group_ref}
        -- scroll to top so button 1 is the newest
        repeat 20 times
            perform action "AXScrollUpByPage" of theGroup
        end repeat
        delay 0.3

        set btnCount to count of buttons of theGroup
        set results to {% raw %}{{}}{% endraw %}
        repeat with i from 1 to btnCount
            set btnRef to button i of theGroup
            set btnName to ""
            set btnDate to ""
            try
                set btnName to value of text field 1 of group 1 of btnRef
            end try
            try
                set btnDesc to description of btnRef
                if btnDesc contains ", " then
                    set AppleScript's text item delimiters to ", "
                    set descParts to text items of btnDesc
                    set AppleScript's text item delimiters to ""
                    if (count of descParts) > 1 then
                        set btnDate to item 2 of descParts
                    end if
                end if
            end try
            if btnName is not "" then
                copy (i as text) & tab & btnName & tab ¬
                    & btnDate to end of results
            end if
        end repeat
        set AppleScript's text item delimiters to linefeed
        return results as text
    end tell
end tell
'''
    items = []
    for line in run_applescript(script).splitlines():
        parts = line.strip().split("\t")
        if len(parts) >= 2:
            items.append({
                "position": int(parts[0]),
                "name": parts[1].strip(),
                "date": parts[2].strip() if len(parts) > 2 else "",
            })
    return items
```

A few things to note:

- **Scrolling to top first** is essential. Without it, the button indices don't correspond to
  the visible items, and you get stale data from offscreen elements.
- **The recording date** comes from the button's `description` attribute, not a separate text
  field. It's embedded after the name, separated by a comma.
- **The 13-group depth** is specific to macOS Sequoia (15.x). Earlier macOS versions may have
  different nesting depths. Use Accessibility Inspector (`/Applications/Utilities/`) to check.

---

## Step 2: Exporting Audio via Clipboard

The next challenge: getting the audio data out. There's no `osascript` command to save a Voice
Memo to a file. But Cmd+C in Voice Memos copies the audio data to the clipboard -- including
the raw M4A bytes.

```python
def select_and_copy(name: str, ui_delay: float = 0.5) -> None:
    """Find a recording by name, select it, and Cmd+C."""
    group_ref = "window 1"
    for _ in range(13):
        group_ref = f"group 1 of {group_ref}"

    escaped = name.replace("\\", "\\\\").replace('"', '\\"')
    script = f'''
tell application "VoiceMemos" to activate
delay {ui_delay}
tell application "System Events"
    tell process "VoiceMemos"
        set theGroup to {group_ref}
        set btnCount to count of buttons of theGroup
        repeat with i from 1 to btnCount
            set btnRef to button i of theGroup
            set btnName to ""
            try
                set btnName to value of text field 1 of group 1 of btnRef
            end try
            if btnName is "{escaped}" then
                perform action "AXPress" of btnRef
                delay {ui_delay * 2}
                keystroke "c" using command down
                delay {ui_delay}
                return "ok"
            end if
        end repeat
    end tell
end tell
return "not-found"
'''
    result = run_applescript(script)
    if result != "ok":
        raise RuntimeError(f"Recording not found: {name}")
```

Then save the clipboard audio data directly to an M4A file:

```python
from pathlib import Path


def save_clipboard_audio(target_path: Path) -> int:
    """Save M4A audio data from clipboard to file. Returns bytes."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    escaped = str(target_path).replace('"', '\\"')

    script = f'''
set theData to the clipboard as «class M4A »
set thePath to POSIX file "{escaped}"
set theFile to open for access thePath with write permission
write theData to theFile
close access theFile
return "ok"
'''
    run_applescript(script)
    return target_path.stat().st_size
```

The magic here is `the clipboard as «class M4A »`. AppleScript's clipboard can hold typed data,
and Voice Memos puts the audio in the `M4A ` class. The `«class»` syntax is AppleScript's way
of referencing four-character type codes. This avoids the Finder entirely -- no drag-and-drop
simulation, no save dialogs, just direct clipboard-to-file transfer.

---

## Step 3: Transcription with mlx-whisper

Now for the AI part. [mlx-whisper][mlx-whisper] is a port of OpenAI's Whisper to Apple's
[MLX framework][mlx], which runs inference directly on the Apple Silicon GPU and Neural Engine.
It's significantly faster than running Whisper through PyTorch on the same hardware.

The script uses [PEP 723 inline metadata][pep723], so `uv run` handles dependencies
automatically -- no virtual environment setup needed:

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "mlx-whisper>=0.4",
# ]
# ///

import sys
from pathlib import Path

# HuggingFace repo ID (auto-downloaded on first run, ~1.6 GB)
MODEL = "mlx-community/whisper-large-v3-turbo"


def transcribe(audio_file: Path, language: str | None = None) -> str:
    """Transcribe audio using mlx-whisper on Apple Silicon."""
    import mlx_whisper

    result = mlx_whisper.transcribe(
        str(audio_file),
        path_or_hf_repo=MODEL,
        language=language,
    )
    return result.get("text", "").strip()


if __name__ == "__main__":
    audio = Path(sys.argv[1])
    print(transcribe(audio))
```

Save this as `transcribe.py` and run:

```bash
uv run transcribe.py recording.m4a
```

On first run, `uv` creates an isolated environment, installs `mlx-whisper` and its dependencies,
and downloads the model from HuggingFace. Subsequent runs reuse the cached environment and
model. The [PEP 723][pep723] `# /// script` block tells `uv` exactly which dependencies are
needed -- no `requirements.txt`, no `pyproject.toml`, just the script itself.

### Why mlx-whisper?

Three reasons:

1. **Speed.** On an M4 Max, `whisper-large-v3-turbo` transcribes ~10x faster than real-time.
   A 10-minute memo takes under 60 seconds. On an M1, it's roughly 1x real-time.
2. **Memory efficiency.** MLX uses unified memory, so the model loads directly into GPU-accessible
   RAM. No copying between CPU and GPU memory.
3. **Zero configuration.** No server to run. No Docker container. No GPU drivers. Import the
   library, call one function, get text.

### The Model: whisper-large-v3-turbo

The `whisper-large-v3-turbo` model is a distilled version of Whisper large-v3 that's ~4x faster
with minimal quality loss. It supports 99 languages out of the box. The MLX-optimized version
is hosted at [mlx-community/whisper-large-v3-turbo][mlx-model] on HuggingFace.

| Property         | Value                                     |
|------------------|-------------------------------------------|
| **Model size**   | ~1.6 GB (FP16)                            |
| **Parameters**   | 809M                                      |
| **Languages**    | 99                                        |
| **Architecture** | Encoder-decoder transformer (distilled)   |
| **Speed (M1)**   | ~1x real-time                             |
| **Speed (M4 Max)** | ~10x real-time                          |

---

## Alternative: Transcription with Ollama

If you prefer a server-based approach -- or want to use an NVIDIA GPU -- [Ollama][ollama] also
supports Whisper models. This is useful if you already run Ollama for LLM inference and want a
single tool for everything.

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests>=2.32"]
# ///

import mimetypes
from pathlib import Path
import requests

OLLAMA_URL = "http://127.0.0.1:11434"
# Ollama uses short model names (no HuggingFace org prefix)
OLLAMA_MODEL = "whisper-large-v3-turbo"


def transcribe_with_ollama(
    audio_file: Path,
    model: str = OLLAMA_MODEL,
    language: str | None = None,
    timeout: int = 300,
) -> str:
    """Transcribe audio via local Ollama Whisper API."""
    mime = mimetypes.guess_type(audio_file.name)[0] \
        or "application/octet-stream"

    for endpoint in ["/v1/audio/transcriptions", "/api/transcribe"]:
        data = {"model": model}
        if language:
            data["language"] = language
        try:
            with audio_file.open("rb") as f:
                resp = requests.post(
                    f"{OLLAMA_URL}{endpoint}",
                    data=data,
                    files={"file": (audio_file.name, f, mime)},
                    timeout=timeout,
                )
            if resp.ok:
                text = resp.json().get("text", "").strip()
                if text:
                    return text
        except requests.RequestException:
            continue

    raise RuntimeError(f"Transcription failed for {audio_file}")
```

To set up Ollama for Whisper:

```bash
# Install Ollama (https://ollama.com)
ollama pull whisper-large-v3-turbo
ollama serve  # Starts on port 11434
```

The Ollama approach tries two API endpoints: the OpenAI-compatible `/v1/audio/transcriptions`
and Ollama's native `/api/transcribe`. Note that Whisper support in Ollama is relatively new
and endpoint availability may vary between versions -- I tested with Ollama 0.6.x. If one
endpoint fails, the script falls back to the other.

It also supports a language fallback chain -- try auto-detect first, then fall back to specific
languages:

```python
LANGUAGES = [None, "ru", "en"]  # auto -> Russian -> English

text = ""
for lang in LANGUAGES:
    try:
        text = transcribe_with_ollama(audio, language=lang)
        break
    except RuntimeError:
        continue
```

This is particularly useful for multilingual recordings. I record memos in both English and
Russian, and the auto-detect works well for about 90% of cases. The fallback chain catches
the rest.

### mlx-whisper vs Ollama: When to Use Which

| Factor               | mlx-whisper                   | Ollama                          |
|----------------------|-------------------------------|---------------------------------|
| **Setup**            | `uv run` -- zero config       | Install Ollama + pull model     |
| **Platform**         | Apple Silicon only             | macOS, Linux, Windows           |
| **GPU**              | Apple Neural Engine / GPU      | Apple GPU, NVIDIA CUDA          |
| **Server required**  | No                             | Yes (ollama serve)              |
| **Speed (M4 Max)**  | ~10x real-time                 | ~6-8x real-time                 |
| **Best for**         | MacBook-only pipelines         | Multi-platform, existing Ollama |

My recommendation: use mlx-whisper for a pure-Mac setup. Use Ollama if you already run it for
LLM inference or need NVIDIA GPU support.

---

## Putting It All Together

Here's the complete pipeline as a single `uv run`-able script. It lists memos, exports audio,
and transcribes -- all in one pass:

```python
#!/usr/bin/env python3
"""Voice memo transcription pipeline. Run: uv run pipeline.py"""

# /// script
# requires-python = ">=3.11"
# dependencies = ["mlx-whisper>=0.4"]
# ///

import subprocess
from pathlib import Path

OUTPUT_DIR = Path("voice-memos")
MODEL = "mlx-community/whisper-large-v3-turbo"


def run_applescript(script: str) -> str:
    proc = subprocess.run(
        ["osascript", "-"], input=script, text=True,
        capture_output=True, timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip())
    return proc.stdout.strip()


def list_memos() -> list[dict]:
    group_ref = "window 1"
    for _ in range(13):
        group_ref = f"group 1 of {group_ref}"
    script = f'''
tell application "VoiceMemos" to activate
delay 0.5
tell application "System Events"
    tell process "VoiceMemos"
        set theGroup to {group_ref}
        repeat 20 times
            perform action "AXScrollUpByPage" of theGroup
        end repeat
        delay 0.3
        set btnCount to count of buttons of theGroup
        set results to {% raw %}{{}}{% endraw %}
        repeat with i from 1 to btnCount
            set btnRef to button i of theGroup
            set btnName to ""
            try
                set btnName to value of text field 1 of ¬
                    group 1 of btnRef
            end try
            if btnName is not "" then
                copy (i as text) & tab & btnName to end of results
            end if
        end repeat
        set AppleScript's text item delimiters to linefeed
        return results as text
    end tell
end tell
'''
    return [
        {"position": int(p[0]), "name": p[1]}
        for line in run_applescript(script).splitlines()
        if (p := line.strip().split("\t")) and len(p) >= 2
    ]


def export_memo(name: str) -> Path:
    group_ref = "window 1"
    for _ in range(13):
        group_ref = f"group 1 of {group_ref}"
    escaped_name = name.replace('"', '\\"')

    run_applescript(f'''
tell application "VoiceMemos" to activate
delay 0.5
tell application "System Events"
    tell process "VoiceMemos"
        set theGroup to {group_ref}
        set btnCount to count of buttons of theGroup
        repeat with i from 1 to btnCount
            set btnRef to button i of theGroup
            try
                if value of text field 1 of group 1 of btnRef ¬
                    is "{escaped_name}" then
                    perform action "AXPress" of btnRef
                    delay 1
                    keystroke "c" using command down
                    delay 0.5
                    exit repeat
                end if
            end try
        end repeat
    end tell
end tell
''')

    output = OUTPUT_DIR / f"{name}.m4a"
    output.parent.mkdir(parents=True, exist_ok=True)
    escaped_path = str(output).replace('"', '\\"')
    run_applescript(f'''
set theData to the clipboard as \u00ABclass M4A \u00BB
set f to open for access (POSIX file "{escaped_path}") ¬
    with write permission
write theData to f
close access f
''')
    return output


def transcribe(audio: Path) -> str:
    import mlx_whisper
    result = mlx_whisper.transcribe(
        str(audio), path_or_hf_repo=MODEL
    )
    return result.get("text", "").strip()


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    memos = list_memos()
    print(f"Found {len(memos)} voice memo(s)\n")

    for memo in memos:
        name = memo["name"]
        audio = OUTPUT_DIR / f"{name}.m4a"
        transcript = audio.with_suffix(".md")

        # Skip if already transcribed
        if transcript.exists():
            print(f"  Skip (exists): {name}")
            continue

        print(f"  Export: {name}")
        export_memo(name)

        print(f"  Transcribe: {name}")
        text = transcribe(audio)
        # Simple output; the production version adds YAML frontmatter
        transcript.write_text(f"# {name}\n\n{text}\n")
        print(f"  Done: {len(text):,} chars\n")


if __name__ == "__main__":
    main()
```

Run it:

```bash
uv run pipeline.py
```

First run downloads the Whisper model (~1.6 GB). After that, it processes your entire voice memo
library incrementally -- skipping recordings that already have transcripts.

---

## Making It Incremental

The production version of this pipeline adds proper state management. A `state.json` file tracks
which recordings have been fetched and transcribed, when, and with which model:

```json
{
  "version": 4,
  "target_map": {
    "voice-memo-2026-02-13-recording-26": {
      "voice_memo_name": "Recording 26",
      "voice_memo_recording_date_iso": "2026-02-13",
      "target_audio": "voice-memo-2026-02-13.../Recording 26.m4a",
      "status": "success"
    }
  },
  "records": [
    {
      "kind": "transcribe",
      "audio": "voice-memo-2026.../Recording 26.m4a",
      "model": "whisper-large-v3-turbo",
      "language": "en",
      "status": "success",
      "transcript_chars": 8889
    }
  ]
}
```

This enables:

- **Skip-if-done** -- don't re-transcribe recordings that haven't changed.
- **Date cutoffs** -- only process recordings from the last N days or after a specific date.
- **Audit trail** -- see exactly when each recording was processed and with which model.
- **Model upgrades** -- when a better Whisper version comes out, force re-transcription with
  `--force` and compare results.

---

## The Output: Searchable Markdown

Each transcript is saved as a markdown file with YAML frontmatter, compatible with
[Obsidian][obsidian], Logseq, or any markdown-based knowledge system:

```markdown
---
created: 2026-02-13
source: "[[Recording 26.m4a]]"
model: mlx-community/whisper-large-v3-turbo
tags:
  - voice-memo
  - transcript
---

# Recording 26

The transcript text appears here. Whisper adds punctuation
and capitalization automatically, which makes the output
surprisingly readable for raw speech-to-text.
```

Now you can `grep` your voice memos. Search for that product idea from three weeks ago. Find
the meeting where someone mentioned that deadline. Your voice recordings become part of your
searchable knowledge base.

---

## Practical Tips

After running this pipeline on 20+ recordings, here are the things I learned:

### UI Automation Is Fragile

AppleScript UI automation breaks when macOS updates change the accessibility tree. The 13-group
depth for Voice Memos is specific to macOS Sequoia. Keep Accessibility Inspector handy for
debugging -- it shows the exact hierarchy.

**Tip:** Add configurable delays between UI actions. On slower machines or when the system is
busy, the default 0.5-second delay isn't enough. The production script uses `--ui-delay` to
tune this.

### When Things Go Wrong

A few failure modes I've encountered and how the production script handles them:

- **Clipboard contains text, not audio.** If the memo selection fails, Cmd+C copies the name
  as text. The script checks whether the clipboard matches the expected memo name before saving.
  If it does, that means the audio wasn't copied -- retry.
- **Accessibility permission revoked.** macOS occasionally resets Accessibility permissions
  after system updates. The script will fail with a cryptic AppleScript error. Check System
  Settings first.
- **Duplicate memo names.** Voice Memos allows multiple recordings with the same name. The
  production script includes the recording date in the folder name
  (`voice-memo-2026-02-13-recording-26/`) to avoid collisions.
- **Model download fails.** The first `mlx-whisper` run downloads ~1.6 GB from HuggingFace.
  If the download is interrupted, delete the HuggingFace cache
  (`~/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/`) and try again.

### Multi-Language Support

Whisper handles language detection automatically, but it's not perfect. For recordings that mix
languages (common if you're multilingual), a fallback chain helps:

```python
LANGUAGES = [None, "ru", "en"]  # auto -> Russian -> English

for lang in LANGUAGES:
    try:
        text = transcribe(audio, language=lang)
        if text:
            break
    except RuntimeError:
        continue
```

Try auto-detect first. If it fails or produces garbage, force a specific language. This
catches about 95% of cases in my experience.

### Run It Overnight

The first run through a large library takes time. Whisper large-v3-turbo on an M1 processes
audio at roughly 1x real-time. If you have 10 hours of recordings, that's 10 hours of
processing. Queue it up before bed:

```bash
# The production script supports --since for date filtering:
uv run scripts/fetch_voice_memos.py --since 2025-01-01 2>&1 | tee transcription.log
```

Subsequent runs only process new recordings and finish in seconds.

### Keep the Original Audio

Always keep the `.m4a` files alongside the transcripts. Whisper is good, but not perfect --
especially for technical jargon, proper nouns, and domain-specific vocabulary. Having the
original audio lets you spot-check and correct errors.

---

## What This Enables

Once your voice memos are searchable text, interesting workflows emerge:

- **Daily review.** I skim yesterday's transcripts over morning coffee. Last week, I recovered
  a product architecture idea I'd completely forgotten about from a 3-minute walk recording.
- **Knowledge base.** Import transcripts into Obsidian and link them to projects, people, ideas.
- **LLM summarization.** Feed transcripts to a local LLM (via Ollama) for summaries, action
  items, or topic extraction. A 30-minute brainstorm session becomes a 10-line summary in
  seconds.
- **Semantic search.** Index transcripts in a vector database (pgvector, Chroma) for
  similarity search across your entire recording history.

The pipeline from voice memo to searchable, AI-processable text is the starting point. What
you build on top is where it gets interesting.

---

## The Bigger Picture: Building a Personal Knowledge Base

This voice memo pipeline is one piece of a larger system I'm building -- a fully local personal
knowledge base. The transcripts land in an [Obsidian][obsidian] vault alongside meeting notes,
bookmarks, annotated PDFs, and research clippings. Multiple scripts and AI models work together
to manage, update, and connect this growing collection.

The architecture behind it:

- **Voice memos** get transcribed by Whisper (this post) and stored as markdown.
- **A RAG pipeline** indexes all markdown files into a [pgvector][pgvector] database -- chunked,
  embedded, and searchable by semantic similarity. When I need to find "that idea about caching
  from last month," I query the RAG system instead of grepping through hundreds of files.
- **Multiple AI scripts** maintain the knowledge base: one summarizes long transcripts, another
  extracts action items, a third generates topic tags and cross-links between related notes.
- **Everything runs locally** on the MacBook. For the broader knowledge base I use Ollama,
  which handles both Whisper transcription and LLM inference for summarization under one
  server. For the standalone voice memo pipeline in this article, mlx-whisper is the simpler
  choice. The vector database runs in a Docker container with pgvector.

The core insight: **AI is most useful when it automates your personal routines, not just code
generation.** Transcription is a mundane task that took zero creativity but consumed real time.
Now it runs in the background while I sleep. Summarization, tagging, and cross-linking happen
automatically. The knowledge base grows and organizes itself.

That's the kind of Local AI use case that justifies the hardware investment -- not benchmarks,
not leaderboards, but saving 30 minutes a day on something you actually do.

I'm planning to write more about this system. Next up: either the **RAG pipeline with pgvector**
or the **Obsidian integration and auto-tagging**. If one of these interests you more -- **let
me know**. Ping me on [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) or
[Twitter/X](https://x.com/jonnyzzz). Your questions genuinely help me prioritize what to
write next.

---

## References

- [OpenAI Whisper][whisper] -- the original speech recognition model
- [mlx-whisper on PyPI][mlx-whisper] -- Apple Silicon optimized Whisper
- [MLX framework][mlx] -- Apple's machine learning framework for Apple Silicon
- [mlx-community/whisper-large-v3-turbo][mlx-model] -- the HuggingFace model
- [Ollama][ollama] -- local LLM and Whisper inference server
- [uv][uv-install] -- fast Python package manager by Astral
- [PEP 723][pep723] -- inline script metadata for self-contained Python scripts
- [Obsidian][obsidian] -- markdown-based knowledge management

*Have questions about running this on your hardware? Found a bug? Reach out on
[LinkedIn](https://www.linkedin.com/in/jonnyzzz/) or
[Twitter/X](https://x.com/jonnyzzz).*

[whisper]: https://github.com/openai/whisper
[mlx-whisper]: https://pypi.org/project/mlx-whisper/
[mlx]: https://ml-explore.github.io/mlx/
[mlx-model]: https://huggingface.co/mlx-community/whisper-large-v3-turbo
[ollama]: https://ollama.com
[uv-install]: https://docs.astral.sh/uv/
[pep723]: https://peps.python.org/pep-0723/
[obsidian]: https://obsidian.md
[pgvector]: https://github.com/pgvector/pgvector