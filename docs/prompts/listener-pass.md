# Listener pass: what only a listener can tell

An agent here can read pictures and measure sound, but can't hear it. Speech-to-text on this PC
(`tools/verify/transcribe.py`) gives the words and their times, and `tools/verify/study.py` shows where the sound
hits. Neither can say *what* a sound is: a TTS voice or a person, a
phonk beat or a lullaby, a vine boom or a door slam. This prompt asks a model that can hear.

## How to run it

1. In an assistant that can listen to an attached video's soundtrack, start a new chat.
2. Attach up to 4 videos from `refs/<set>/videos/` (one at a time for anything over 60 s). Smaller batches give more
   precise times.
3. Paste the prompt below and send.
4. Save each object of the JSON it returns as `refs/<set>/listener/<NNN>.json` (the first three characters of the file
   name), or paste the whole answer back to the agent and it will file them.

Repeat until every video has a file. Check one answer against the transcript before trusting the rest: if its times
are off by more than half a second, ask it to redo that video alone.

## The prompt

```text
You are an expert audio post-production analyst and short-form video editor. I've attached YouTube Shorts: animated
Roblox comedy and story skits, each with over a million views. I can already see their pictures and read a transcript
of the words. I need what only a listener can tell me. Listen to each video's whole soundtrack carefully, more than
once, and describe it precisely.

Return ONE JSON array with one object per attached video, in the order attached, and nothing else. Each object has
exactly these fields:

{
  "file": "<the attached file's name>",
  "voices": [
    {
      "who": "narrator, or the character as seen on screen (e.g. 'red-haired mom')",
      "first_words": "the first few words this voice says",
      "kind": "human recording | text-to-speech | AI voice clone | unsure",
      "sounds_like": "if TTS or AI: which engine or stock voice it most resembles (CapCut, TikTok, ElevenLabs, etc.) and how sure you are; else null",
      "gender_age_impression": "",
      "accent": "",
      "pitch_or_speed_effect": "none | pitched up | pitched down | sped up | slowed | chipmunk | other (say what)",
      "other_effects": "reverb, echo, phone or radio filter, distortion, none",
      "energy_1_to_10": 0,
      "delivery": "e.g. deadpan, exasperated, whiny, hype, sarcastic, soft, scared, sincere",
      "timing_notes": "where it speeds up, slows down or pauses to land a joke or a feeling, with times"
    }
  ],
  "one_voice_plays_several_characters": "yes/no, and how they're told apart (pitch, effect, accent)",
  "music": [
    {
      "start": "m:ss.s", "end": "m:ss.s",
      "description": "genre, instruments, mood (e.g. 'slowed phonk, heavy 808s, menacing')",
      "tempo_bpm": 0,
      "has_vocals": false,
      "identified_track": "artist - title ONLY if you are confident; else null",
      "lyrics_heard": "any words you can make out, else null",
      "level_against_voice": "much quieter | quieter | equal | louder | no voice",
      "dips_under_voice": false,
      "how_it_follows_the_story": "where it starts, stops, drops out, switches or hits, and on what picture or line"
    }
  ],
  "sound_effects": [
    {
      "t": "m:ss.s",
      "sound": "what it is (whoosh, pop, ding, slap, footsteps, door, bell, camera shutter, crowd laugh, scream, ...)",
      "meme_name": "its common internet name if it's a known meme sound (vine boom, bruh, record scratch, 'oh no', ...), else null",
      "purpose": "punchline | transition | emphasis | action | ambience | reaction",
      "loudness": "subtle | medium | loud"
    }
  ],
  "ambience": "room tone, classroom chatter, wind, crickets, rain, traffic, none ...",
  "silences": [ { "t": "m:ss.s", "length_s": 0.0, "purpose": "comedic pause | tension | breath | none" } ],
  "sync_with_picture": "how sound lines up with the cuts and actions: cuts on beats? effects on face changes? music hits on reveals? give times",
  "faces_and_mouths": "do the characters' mouths or faces change while they talk? how?",
  "comedic_or_emotional_timing": "the moments where timing makes a joke land or a feeling hit, with times, and why",
  "first_3_seconds": "exactly what is heard in the first 3 seconds, and why it grabs a scroller",
  "ending": "how the sound ends; does it loop cleanly back into the start?",
  "mix": "overall loudness feel, voice clarity, bass, compression, anything harsh or muddy",
  "why_the_sound_works": ["3 to 5 short points"],
  "unsure_about": "anything you couldn't make out"
}

Rules:
- Times are m:ss.s from the start of that video.
- List every sound effect you can hear, quiet ones too. If there is no voice, or no music, say so with an empty list.
- Never invent a song title or artist: null unless you're sure. Lyrics you heard are more useful than a guess.
- Return only the JSON array: no prose before or after it.
```
