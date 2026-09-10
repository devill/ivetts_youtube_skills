# `actions.json` — the judgment

`build_data.py` produces the facts. This file is the opinion, and you write it by hand after
reading the outros. Path: `<work dir>/data/actions.json`.

Every id is a YouTube video id that appears in `data/graph.json`. An id that is not there stops
the build.

## Shape

```json
{
  "destinations": ["<video id>", "..."],
  "unmet":  [{"id": "", "said": "", "gap": "", "fix": ""}],
  "stale":  [{"id": "", "said": "", "delivered": "<video id>", "fix": ""}],
  "free":   [{"id": "", "outro": "", "target": "<video id> or null"}],
  "trim":   [{"id": "", "why": "", "fix": ""}],
  "thumbnails": [{"id": "", "note": ""}],
  "plan":   [{"id": "", "do": "", "why": "", "effort": "5 min | 15 min | session"}]
}
```

`said` and `outro` are **verbatim quotes** from the transcript, in quotation marks. Never
paraphrase — an unverifiable finding is one the creator has to go and check themselves, which
is the work you were meant to save them.

## The buckets

**`destinations` — where to send people.**
Recent videos that hold attention once someone arrives: high average view duration and
percentage. Views do not qualify a destination; watch time does. Every recommendation anywhere
else in the file points at one of these.

**`unmet` — promises with nothing behind them.**
The outro names a follow-up that was never released, or points at a video viewers cannot watch
(unlisted, private, deleted, or a placeholder upload). `gap` says what is missing; `fix` names
the closest released neighbour to pin until the real thing exists.

**`stale` — promise kept, end screen never updated.**
The follow-up shipped. The end screen still does not point at it. `delivered` is its id.
These are the cheapest wins on the channel: the right video already exists.

**`free` — outros that fit any link.**
Nothing specific is promised out loud, so the end screen can point anywhere without
re-recording a second of audio. `target` is the video to pin, or `null` when what is pinned
today is already right.

**`trim` — outros worth trimming.**
Dated plugs and promises that pin the ending to a moment that has passed: an event last year,
a "next video" that stopped making sense. Cutting the sentence frees the end screen to match
anything, and turns a `unmet` item into a `free` one.

**`thumbnails` — packaging worth redoing.**
Low click-through rate with healthy watch time. People who click stay, so the thumbnail is what
costs the views, not the video.

> **Never nominate an outlier.** A video with impressions far above the channel's normal was
> pushed way outside the channel's audience, and its low CTR measures strangers scrolling past,
> not bad packaging. Rule of thumb: skip anything whose thumbnail impressions are three times
> the channel median or more. Repackaging it chases an audience that was never yours.

**`plan` — one a day, highest leverage first.**
Every other bucket, flattened and ordered by what the change is worth, not by how long it
takes. `do` is the instruction, in the imperative, specific enough to carry out in Studio
without re-reading anything. `effort` is one of `5 min`, `15 min`, `session`.

Mix the efforts deliberately. A run of `session` items in a row is a plan that gets abandoned;
the creator should always be able to find a five-minute item on a low-energy day.

## Choosing a destination

1. **Somewhere that holds attention.** From `destinations`, always.
2. **The next step, not the same step.** Never point at a video that covers essentially the
   same ground as the source in a slightly newer or older version. It reads as a rerun, wastes
   the slot, and the viewer who stayed to the end has already had that information. Send them
   forward.
3. **Honour what the outro says.** If the words promise a specific thing, the link must be that
   thing or the words have to go (see `trim`).
4. **Old to new.** The point of the exercise is the back catalogue feeding the videos that are
   working now.

## Writing the copy

- Short sentences. No hedging.
- `fix` and `do` are instructions someone can follow in Studio, not observations.
- Name videos by title, in quotes. The creator does not think in video ids.
- If a video is already correct, say so and leave it. A worklist padded with non-work is a
  worklist nobody finishes.
