---
name: endscreen-audit
description: Audit a YouTube channel's end screens — build one page showing which published long-form video links to which, with lifetime stats, and a prioritised worklist of the repairs worth making (broken promises in outros, end screens never updated after the follow-up shipped, outros that pin a video to a moment that has passed). Use when someone asks to map, audit, fix or optimise their end screens, asks where their videos send viewers next, wants their back catalogue to feed their best videos, or says their old videos point at nothing.
---

# End screen audit

Turn a channel's end screens into one page: a map of what points where, and a list of the
repairs worth doing, one a day, highest leverage first.

Everything runs in a **work directory** the creator picks (default `endscreen-audit/` in the
current directory). Scripts live in this skill; data and the finished page live in the work
directory. `--work DIR` on every script.

## What the page shows

- **Map** — one card per published long-form video (Shorts, unlisted and private excluded),
  arrows for the links the creator **pinned**, lifetime stats on hover, cards draggable so
  arrows can be untangled.
- **Repairs** — the worklist, ordered by leverage, each item naming the video, what its outro
  says out loud, and the smallest change that closes the gap.

Auto slots ("Best for viewer", "Most recent upload") are never drawn as arrows. YouTube fills
them differently for every viewer, so they are not a link the creator made. They are counted
separately.

## Before anything: three things only a human can do

Ask for all three at once, then stop until they are done.

1. **A Google OAuth client.** Google Cloud Console → enable **YouTube Data API v3** and
   **YouTube Analytics API** → Credentials → OAuth client ID → **Desktop app** → download the
   JSON → save it as `<work dir>/client_secret.json`.

   The work directory now holds an OAuth client secret, and shortly a refresh token. Add it to
   `.gitignore` before anything else.
2. **Consent, in a normal terminal** (it opens a browser, and a consent screen nobody is
   watching is a hung session):

       python3 -m pip install google-api-python-client google-auth-oauthlib
       python3 <skill dir>/scripts/auth.py --work <work dir>

3. **The lifetime stats export.** YouTube Studio → Analytics → Advanced mode → date range
   **Lifetime** → Content tab → Export → CSV. Unzip it and put `Table data.csv` at
   `<work dir>/data/csv/Table data.csv`.
   This is the only source of click-through rate. No Google API exposes thumbnail impressions
   or CTR — do not go looking for one.

## Collect

Run from anywhere; every script takes `--work DIR`.

    python3 <skill dir>/scripts/fetch_videos.py --work DIR       # every upload + channel identity
    python3 <skill dir>/scripts/classify_shorts.py --work DIR    # Short or long-form, one HEAD each
    python3 <skill dir>/scripts/fetch_analytics.py --work DIR    # engaged views, avg view duration and %
    python3 <skill dir>/scripts/fetch_transcripts.py --work DIR  # one caption track per long-form video

`classify_shorts.py` only fills in ids it has not seen, so it is cheap to re-run. It writes
`data/is_short.json` and `data/long_form.json` — the public long-form ids everything
downstream reads. Run it before the analytics and transcript steps.

### End screens, from Studio

The slow part, and the only part that needs a browser.

**The public watch page is not a substitute.** It resolves auto slots into concrete videos, so
a scraped map invents links the creator never made. Studio is the only place the difference
survives.

Two conditions before starting:

- The Studio tab must be on the right channel. Read `window.ytcfg.get('CHANNEL_ID')` and
  compare it with `data/channel.json`. If it differs, ask the human to switch account in
  Studio — the account chooser is a Google iframe that page scripting cannot reach.
- **The tab must be visible on screen.** Chrome will not render Studio's video editor in a
  hidden tab, and the end-screen rows come back empty with no error.

For each id in `data/long_form.json`, in batches of about four, navigate to
`https://studio.youtube.com/video/<id>/editor` and poll for the rows:

    let rows=[],tl=false;
    for(let i=0;i<20;i++){
      await new Promise(r=>setTimeout(r,1000));
      rows=[...document.querySelectorAll('ytve-endscreen-row')];
      tl=tl||!!document.querySelector('ytve-endscreen-editor-timeline');
      if(rows.length)break;
    }
    ({v:location.pathname.split('/')[2],timeline:tl,
      rows:rows.map(r=>(r.innerText||'').replace(/\s+/g,' ').trim())})

- **Full navigation, never in-page routing.** Clicking an internal link switches the URL but
  leaves the previous video's rows on screen, so you read the wrong video's end screen.
- **An empty result only counts when `timeline` is true.** That means the track rendered and
  genuinely holds nothing. `timeline: false` means the editor never loaded — retry.
- Going too fast trips a rate limit and every video after it reads empty. Pace the batches.

Rows look like `Subscribe: <channel>`, `Video: <title>`, `Playlist: <name>`, and for auto slots
exactly `Video: Best for viewer` or `Video: Most recent upload`. Write
`data/studio_endscreens.json` as `{"<video id>": ["<row>", ...]}` — one entry per id in
`long_form.json`, empty lists included.

## Judge

    python3 <skill dir>/scripts/build_data.py --work DIR   # -> data/graph.json

`build_data.py` stops and prints the config snippet to add when a row names a video it cannot
find — an end screen pointing at another channel, or at a conference talk.

Now read the outros and write `data/actions.json` yourself. This is the part no script can do.
The schema is in `reference/actions.md`, and so are the rules for each bucket. Read it before
writing a line of JSON.

The short version:

- Read the **last ~90 seconds** of each transcript in `data/transcripts/`. That is where the
  promise lives.
- Quote what the outro actually says, verbatim. A paraphrase makes the finding unverifiable
  and the creator will not trust it.
- Every recommendation names a concrete destination video, chosen by the rules in
  `reference/actions.md`.

## Build

    python3 <skill dir>/scripts/build_page.py --work DIR

Writes `<work dir>/end-screen-audit.html` — one self-contained page, offline, light and dark,
thumbnails embedded. Open it, do not just declare it built.

If the creator wants it as a shareable link, publish `<work dir>/data/artifact.html` with the
Artifact tool. Keep the local file either way: an artifact URL dies without internet.

## Re-running later

After publishing a video or changing end screens in Studio, re-run the collect steps, redo the
Studio read for the videos that changed, and rebuild. The judgment in `actions.json` is worth
revisiting whenever a promised follow-up ships — that is exactly what turns an item from
"promise with nothing behind it" into "promise kept, end screen never updated".
