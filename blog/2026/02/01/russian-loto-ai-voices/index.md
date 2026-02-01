# Russian Loto with AI Celebrity Voices

**Date:** February 01, 2026  
**Author:** Eugene Petrenko  
**Tags:** ai, tts, python, qwen, voice-cloning

---

Hey Siri, can you count from 1 to 90 in random order? Siri could not. But Russian Loto absolutely
needs it: a caller shuffles 1-90 and announces each number as people mark their tickets.

If you never played Loto/Bingo, this explainer shows the call-and-mark loop:
[Learn Numbers Playing Lotto (Bingo) (Games in Russian for complete beginners)][loto-video].

I challenged Claude to build the game in 10 minutes. Then, in the next 20 minutes, I had Qwen TTS
running locally on my Mac with AI celebrity voices. It was fast to invent, and it turned into
great family fun.

[loto-video]: https://www.youtube.com/watch?v=H1tQs2vXnQg

The result: [jonnyzzz-loto](https://github.com/jonnyzzz/jonnyzzz-loto) — a Russian Loto game where
12 AI-generated celebrity voices announce numbers with character-specific jokes.

## The Problem with Real Loto

Family gatherings with Russian Loto have a problem: the person calling numbers gets bored. They
read monotonously. The game becomes a chore. What if the announcer was actually entertaining?

The obvious solution: record celebrity-like voice samples and use voice cloning. But that requires
finding clean audio samples, dealing with licensing concerns, and building a pipeline for each
celebrity. Too much work for a weekend prototype.

## Qwen3-TTS and VoiceDesign

Alibaba's [Qwen3-TTS](https://huggingface.co/Qwen/Qwen2.5-Omni-3B) changed everything. This
open-source model (Apache 2.0) has a fascinating capability called VoiceDesign — instead of
cloning a voice from audio samples, you describe the voice in text and the model generates it.
That is exactly what rapid prototyping needs: a prompt, a quick run, a new character.

No samples needed. Just a text description like:

> "A deep elderly male Russian voice, slow deliberate speech with long pauses, authoritative
> Soviet leader tone, slight speech impediment"

And outcomes something that sounds like Brezhnev. Not a clone — but a convincing character voice
that captures the essence.

## The Tech Stack

The project runs entirely locally on Mac with Apple Silicon, optimized for short iteration loops:

```bash
# Setup (creates venv, installs dependencies)
./setup_qwen_mac.sh

# Run with AI voices
uv run python loto.py --qwen
```

**Stack:**
- Python with [uv](https://github.com/astral-sh/uv) package manager
- Qwen3-TTS for speech synthesis
- MPS (Metal Performance Shaders) for GPU acceleration on Apple Silicon
- pygame for audio playback
- VoiceDesign model for text-to-voice-description synthesis

The setup script handles PyTorch with MPS support, the transformers library, and audio
dependencies. First run downloads the model (~3GB).

## 12 Celebrity Voices Random Pick (Claude-Generated)

Each character has a unique voice description and personality:

| Character | Voice Description | Style |
|-----------|------------------|-------|
| Leonid Brezhnev | Deep elderly male, slow deliberate speech, Soviet gravitas | Turns everything into five-year plan references |
| Maxim Galkin | Theatrical, energetic showman, perfect diction | Game show host enthusiasm |
| Alla Pugacheva | Mature female, pop diva, dramatic pauses | Primadonna drama for every number |
| Vinni-Puh (Evgeny Leonov) | Warm, friendly, childlike wonder | Honey and friendship references |
| Vladimir Zhirinovsky | Passionate, loud, political fervor | Makes everything a political statement |
| Monetochka | Young female, indie pop, Gen-Z slang | "Это вайб!" for random numbers |
| Korol i Shut (Gorshok) | Theatrical punk rock, horror imagery | Gothic humor, Friday the 13th |
| Vladimir Vysotsky | Raspy, intense, poetic bard | Every number becomes existential |
| Sergey Shnurov (Leningrad) | Rock provocateur, irreverent, mocking | Makes fun of the game itself |
| Filipp Kirkorov | Grandiose pop king, over-the-top | Everything is a grand celebration |
| Grigory Leps | Rock ballad, emotional, gravelly | Dramatic weight to each number |
| Nikolay Baskov | Operatic tenor, polished, charming | Treats Loto like opera |

## Character-Specific Jokes

The magic isn't just in the voices — each character has jokes tailored to specific numbers. Here
are some examples:

**Brezhnev on 5:**
```
Пять... Пятилетка! Выполним и перевыполним план!
(Five... Five-year plan! We will fulfill and exceed the plan!)
```

**Gorshok (Korol i Shut) on 13:**
```
Тринадцать! Моё любимое число! Ха-ха-ха! Пятница тринадцатое!
(Thirteen! My favorite number! Ha-ha-ha! Friday the 13th!)
```

**Zhirinovsky on any number:**
```
Это число... это символ нашей великой страны!
(This number... this is a symbol of our great country!)
```

**Monetochka on 69:**
```
Ой, это тот самый мем... Найс!
(Oh, that's that meme... Nice!)
```

The character definitions live in Python dataclasses with voice descriptions, typical phrases,
and number-specific joke mappings.

## How VoiceDesign Actually Works

Traditional TTS voice cloning needs audio samples. VoiceDesign takes a different approach:

```python
voice_description = """
A deep elderly male Russian voice speaking with
slow deliberate speech and long dramatic pauses.
Authoritative Soviet leader tone with slight
speech impediment characteristic of late period.
"""

# The model generates voice parameters from the description
# No audio samples required
```

The model was trained to understand voice characteristics from text and synthesize matching
speech. It's not perfect — sometimes the voices drift across utterances. But for a game where
each number is a separate audio clip, it works well.

The Russian language support is surprisingly good. Qwen handles Cyrillic text natively, and the
pronunciation is close enough that native speakers recognize the character archetypes.

## Noise Detection: Making It Interactive

The game includes an experimental feature: ambient noise detection. It listens to the room and
reacts:

```python
# When the room gets quiet, repeat the last number
# Uses exponential backoff to get attention
if ambient_noise < threshold:
    repeat_last_number()
    backoff *= 2
```

This makes the game feel more alive — when people are talking and not paying attention, the AI
announcer waits. When it gets quiet, it calls the next number or repeats. Like a patient game
master.

## Running the Game

Basic usage:

```bash
# Install dependencies
./setup_qwen_mac.sh

# Run with AI voices (first run generates all audio clips)
uv run python loto.py --qwen

# Run with pre-generated voices (faster startup)
uv run python loto.py --qwen --cache

# Select specific character
uv run python loto.py --qwen --character brezhnev
```

First run takes a while — it generates audio for all numbers (1-90) for the selected character.
Subsequent runs with `--cache` start instantly.

## Performance on Apple Silicon

On M1/M2/M3 Macs, the MPS backend provides decent performance:

- Audio generation: ~2-3 seconds per number
- First run (90 numbers): ~3-4 minutes per character
- Cached playback: instant

For comparison, CPU-only inference is 5-10x slower. The MPS optimization in PyTorch makes local
AI TTS practical.

## Lessons Learned

**Family Fun** is easy to achieve. Just a suggent idea gets much easier to implement.

**VoiceDesign is powerful but inconsistent.** The same voice description can produce slightly
different voices across runs. For a game, this adds variety. For production TTS, you'd want more
control.

**Character design matters more than voice quality.** A mediocre voice with great jokes is more
entertaining than a perfect voice reading numbers monotonously. The character personalities
carry the experience.

**#LocalAI for fun projects is here.** No API keys, no cloud costs, no latency. Models like
Qwen3-TTS make creative voice projects accessible to anyone with a decent Mac.

## Try It

The code is at [github.com/jonnyzzz/jonnyzzz-loto](https://github.com/jonnyzzz/jonnyzzz-loto).

Add your own characters. Improve the jokes. Make Brezhnev more authentic. The voice description
format is simple enough that you can experiment without ML expertise.

And if you have a better joke for number 77 (семьдесят семь) — submit a PR.

Find me on [LinkedIn](https://www.linkedin.com/in/jonnyzzz/) or
[Twitter](https://twitter.com/jonnyzzz) if you build something fun with AI voices.

Stay tuned, I will prepare something similar with NVIDIA DGX Spart setup for some conferences in the furure!