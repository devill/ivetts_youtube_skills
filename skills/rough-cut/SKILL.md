---
name: rough-cut
description: Turn raw footage into a rough cut or first cut, transcribe my footage, pick the best takes, assemble a timeline from my takes, handle too much footage, organise talking-head footage with multiple takes, A-roll, string-out, selection workbench, or choose between takes.
---

# Rough cut

Turn many attempts at each talking-head section into one watchable string-out. You refine the result in your own editor; this skill makes the material easy to judge and opens the marked choices as a timeline.

## What lives in the work folder

Use `rough-cut/` in the current directory unless you agree another folder. Keep source transcripts: they are expensive and never deleted.

- `transcripts/<clip>.txt` — one transcript per clip
- `speech.json` — acoustic speech regions and duration
- `candidates.json` — sections in intended final order and their candidate spans
- `selections.json` — use, maybe or reject marks and notes
- `rough-cut.xml`, `rough-cut.fcpxml`, `rough-cut.edl` — the three exports
- `notes.md` — handoff for the next session

The exact contract is:
```json
speech.json: {"clip": {"duration": 12.3, "regions": [[1, 4]]}}
candidates.json: [{"key":"intro", "label":"Intro", "note":"", "candidates":[{"clip":"A","start":1,"end":4,"text":"verbatim","rating":4,"note":""}]}]
selections.json: {"marks":{"A|1.0000":{"state":"use","note":""}}}
```
Always normalise candidate identities as `clip|{float(start):.4f}`.

## Ask before starting

First work out what you can on your own: clip names and count from the folder, durations from a
quick probe, the spoken language from a first transcription pass, and any script, teleprompter
export or GPS tracks sitting beside the footage. Ask the creator only what is still unknown, all
in one message:

1. Which folder is the footage, and which files are in scope? (Only if the folder is ambiguous.)
2. What language is spoken? (Only if you have not worked it out from the footage.)
3. Is there a script of what was meant to be said (teleprompter text)?
4. What should the video's shape be: sections, their order and target length? If they do not know
   yet, propose it from the material later.
5. Which editor do they cut in? This decides which export matters.
6. If an LLM audio pass would use a paid API: the rough cost estimate and a go-ahead.

## 1. Transcribe every clip

Create the work folder and `transcripts/`. Prefer a **subagent with audio input** over Whisper: in
a real edit a Gemini Flash subagent heard four false starts at the top of an intro that Whisper
had silently deleted from its text (`gemini-flash-latest` worked; the numbered `gemini-2.5-flash`
name 404'd). Ask it for a verbatim transcript — false starts, stutters and repeats kept — with
segment timestamps, per speech region. Whisper remains the fallback when there is no audio-capable
model or the footage must stay free and local; its text is then good enough for grouping, but
never for choosing takes. Either way: pass the language explicitly, one transcript per clip. See
`reference/transcription.md`.

## 2. Find true speech regions

Run `scripts/speech_regions.py --media DIR --out WORK/speech.json`. It uses sound, not transcript text. This avoids word-timestamp gaps and catches where a person actually starts and stops.

## 3. Group the takes

Read all transcripts and group attempts by the section they try to say. Use the creator's intended narrative order, not recording order. See `reference/grouping-and-order.md`. Put sections in that order in `candidates.json`.

## 4. Pre-select promising takes

Use an LLM with audio input only as a filter. If the transcripts came from the audio subagent in
phase 1, its verbatim per-attempt output is the judging input — have it rate what it already
heard, and spot-check by ear, instead of re-listening from scratch. Ask for every complete,
cleanly delivered sentence and retain alternate phrasings. Verify every claimed span against the
real timestamps. See `reference/judging-takes.md`. Get approval before paid API use.

## 5. Fix transcript words when useful

If there is a script, correct names, words and punctuation against it. Without one, make a small gazetteer first. Write new fixed files beside the originals. Corrections change what words say, not how fluently they were said, so take judgement always uses audio or the uncorrected transcripts. See `reference/transcript-fixing.md`.

## 6. Let the creator judge

Run `python3 scripts/workbench.py --work WORK --media MEDIA` and open the printed local URL in one browser tab — marks live in one file, and two tabs editing at once can lose each other's marks. The creator watches each candidate and marks use, maybe or reject, with notes. The page autosaves. Rejected and maybe options remain visible.

## 7. Export the timeline

Run `python3 scripts/export_timeline.py --work WORK --media MEDIA`. It writes all three dialects by default. Premiere Pro imports the xmeml v4 file. Final Cut Pro and DaVinci read FCPXML. The CMX3600 EDL is the fallback.

## 8. Hand off

Write `notes.md` with the footage and work paths, what is complete, which marks are still open, export paths, the editor, and questions for the next session.

## Rules that come from real edits

- Whisper transcribes what was said, not how it was said: it silently deletes false starts and
  stutters. A model with audio input does not — prefer it as the transcriber of record, and never
  choose or cut takes from transcript text alone; judge audio.
- Speech-to-text end timestamps are word onsets. Every out-point gets 0.6 seconds of tail. Every in-point gets 0.4 seconds of pre-roll. The player already pads playback.
- Transcripts are expensive source files. Never delete them. Put corrections in new files.
- Group by attempted place, topic or scene, never text similarity. Rephrasing is normal. Most of the time one of the last recordings is best.
- Fewest cuts wins. Prefer a whole section over stitching halves. One or two cuts inside a spoken section is fine; B-roll can cover them later.
- Narrative order comes from the creator's journey, argument or path, not chronology. Metadata can propose it; the creator corrects it. `candidates.json` order is the timeline order.
- The LLM pass pre-selects only complete sentences with a chance of being usable. Taste wins over a small slip. Background noise can often be fixed with dialogue separation.
- Corrected transcript text can hide stutter. Judge audio or uncorrected text.
- Keep usable-but-rejected options visible. Half-sentences are the only candidates to discard outright.
- Verify every LLM time span against real transcript timestamps. Snap or drop fabricated spans.
- Export all three dialects by default: Premiere uses xmeml, Final Cut Pro and DaVinci read FCPXML, and EDL opens almost anywhere.

## Finish

Let the creator mark the workbench, export the timeline, and open it in the chosen editor. Write `notes.md` so a fresh session can continue without repeating transcription or losing the creator's decisions.
