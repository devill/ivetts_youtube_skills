---
name: endscreen-audit
description: Audit a YouTube channel's end screens — build one page showing which published long-form video links to which, with lifetime stats, and a prioritised worklist of the repairs worth making (broken promises in outros, end screens never updated after the follow-up shipped, outros that pin a video to a moment that has passed). Use when someone asks to map, audit, fix or optimise their end screens, asks where their videos send viewers next, wants their back catalogue to feed their best videos, or says their old videos point at nothing.
---

# End screen audit

Turn a channel's end screens into one page: a map of what points where, and a list of the
repairs worth doing, one a day, highest leverage first.

Everything comes out of the creator's own browser, signed in to YouTube Studio. No API key, no
Google Cloud project, no packages to install — the scripts here are Python 3 and its standard
library, nothing else.

Everything is written into a **work directory** the creator picks (default `endscreen-audit/` in
the current directory). Every script takes `--work DIR`. Create the directory and its `data/`
subdirectory before the first browser read, because the browser steps write files into it.

## What the page shows

- **Map** — one card per published long-form video (Shorts, unlisted and private excluded),
  arrows for the links the creator **pinned**, lifetime stats on hover, cards draggable so
  arrows can be untangled.
- **Repairs** — the worklist, ordered by leverage, each item naming the video, what its outro
  says out loud, and the smallest change that closes the gap.

Auto slots ("Best for viewer", "Most recent upload") are never drawn as arrows. YouTube fills
them differently for every viewer, so they are not a link the creator made. They are counted
separately.

## Before anything: three things only the creator can do

1. **Be signed in to YouTube Studio in Chrome**, on the channel being audited.
2. **Leave the browser window visible on screen** for the whole run. Chrome does not render
   Studio's tables or its video editor in a hidden tab, and they come back empty with no error.
3. **Set Studio's language to English** (Settings → your account → Language). Every read below
   matches Studio's own words — `Public`, the CSV column headers — and a localised Studio makes
   the scripts stop rather than guess.

Then say what is about to happen: the run visits every published video twice, so a channel with
fifty videos takes a while, and the browser is busy throughout.

## 0. The channel

Open `https://studio.youtube.com/`. Read the channel and confirm it is the one they meant —
Studio opens whichever channel the account used last, which on a multi-channel account is
regularly the wrong one. Switching account is a Google iframe that page scripting cannot reach,
so the creator has to do it themselves.

    ({id: ytcfg.get('CHANNEL_ID'),
      title: document.querySelector('#channel-title, ytcp-navigation-drawer #entity-name')?.innerText.trim()})

Write it to `<work dir>/data/channel.json` as `{"id": "...", "title": "..."}`. The title becomes
the page's heading; the id is in every Studio URL below.

## Collect

### 1. Every upload, from the Content page

Three tabs hold published videos, and all three matter:

- `https://studio.youtube.com/channel/<CHANNEL_ID>/videos/upload` — ordinary videos
- `https://studio.youtube.com/channel/<CHANNEL_ID>/videos/short` — Shorts
- `https://studio.youtube.com/channel/<CHANNEL_ID>/videos/live` — livestreams and premieres,
  which carry end screens exactly like an ordinary video

On each tab, wait for `ytcp-video-row` elements and read every row:

    let rows=[];
    for(let i=0;i<20;i++){
      await new Promise(r=>setTimeout(r,1000));
      rows=[...document.querySelectorAll('ytcp-video-row')];
      if(rows.length)break;
    }
    rows.map(r=>{
      const a=r.querySelector('a#video-title');
      return {id:(a?.href.match(/video\/([\w-]{11})/)||[])[1],
              title:a?.title||a?.innerText.trim(),
              visibility:r.querySelector('.tablecell-visibility')?.innerText.replace(/\s+/g,' ').trim()};
    })

A tab holds 30 rows at a time. Page through each one with the *next page* arrow at the bottom
until it is disabled, collecting as you go, and do that on all three tabs. **Paging is the most
fragile step in the run** — a page silently skipped is a handful of videos missing from the
finished map. `select_videos.py` cross-checks the result against the analytics export and says
so if the two disagree.

Write `<work dir>/data/videos.json` — `[{"id","title","visibility"}]`, every row from all three
tabs — and `<work dir>/data/shorts.json`, the ids from the Shorts tab alone.

`title` has to be the full title, because an end screen names its target by title and nothing
else. Studio truncates the visible text, which is why the snippet reads the `title` attribute.

### 2. The numbers, from the analytics export

Open Studio → Analytics → **Advanced mode**, set the date range to **Lifetime** and the report
to **Content**. Deep link, which lands on exactly that view:

    https://studio.youtube.com/channel/<CHANNEL_ID>/analytics/tab-overview/period-default/explore?entity_type=CHANNEL&entity_id=<CHANNEL_ID>&time_period=lifetime&explore_type=TABLE_AND_CHART&dimension=VIDEO

**Stop there and hand it over.** Ask the creator to click the download icon at the top right and
choose **Comma-separated values (.csv)**. A download started by browser automation never
completes — Chrome drops it silently, so you will sit and watch for a file that is not coming.
It has to be their click.

They get a zip. Ask them to say when it has saved, then unzip it yourself and put
`Table data.csv` at `<work dir>/data/csv/Table data.csv`.

Check the header row before going on: the first column must be `Content` and the third
`Video publish time`. Anything else means a different report was exported, or Studio is not in
English.

Do not try to read the numbers off the analytics table instead. It looks like it would save the
download, and it does not: the publish-date column comes back empty, some rows carry no video
id, and the figures are formatted for the viewer's locale (`5.110`, `313,6`). The export has all
of it, plainly.

This export is the only source of thumbnail impressions and click-through rate anywhere. No API
exposes them — do not go looking for one.

Then:

    python3 <skill dir>/scripts/select_videos.py --work DIR

It writes `<work dir>/data/long_form.json`, the published long-form ids the next two steps work
through.

### 3. End screens, from Studio

The slow part.

**The public watch page is not a substitute.** It resolves auto slots into concrete videos, so a
scraped map invents links the creator never made. Studio is the only place the difference
survives.

For each id in `long_form.json`, in batches of about four, navigate to
`https://studio.youtube.com/video/<id>/editor` and poll for the rows:

    const start=[...document.querySelectorAll('button, ytcp-button, tp-yt-paper-button')]
      .find(b=>/^get started$/i.test((b.innerText||'').trim()));
    if(start)start.click();
    let rows=[],tl=false;
    for(let i=0;i<25;i++){
      await new Promise(r=>setTimeout(r,1000));
      rows=[...document.querySelectorAll('ytve-endscreen-row')];
      tl=tl||!!document.querySelector('ytve-endscreen-editor-timeline');
      if(rows.length)break;
    }
    ({v:location.pathname.split('/')[2],timeline:tl,
      rows:rows.map(r=>(r.innerText||'').replace(/\s+/g,' ').trim())})

- **The `Get started` click is not optional.** On a channel that has never opened the video
  editor, Studio shows a splash screen instead of the timeline. Nothing renders until it is
  clicked, so the video reads as having no end screen at all when it has a full one. It appears
  per video, not once per channel.
- **Full navigation, never in-page routing.** Clicking an internal link switches the URL but
  leaves the previous video's rows on screen, so you read the wrong video's end screen.
- **An empty result only counts when `timeline` is true.** That means the track rendered and
  genuinely holds nothing. `timeline: false` means the editor never loaded — retry.
- Going too fast trips a rate limit and every video after it reads empty. Pace the batches.

Rows look like `Subscribe: <channel>`, `Video: <title>`, `Playlist: <name>`, and for auto slots
exactly `Video: Best for viewer` or `Video: Most recent upload`. Write
`<work dir>/data/studio_endscreens.json` as `{"<video id>": ["<row>", ...]}` — one entry per id
in `long_form.json`, empty lists included.

### 4. Outros, from the transcript panel

For each id in `long_form.json`, open `https://www.youtube.com/watch?v=<id>`, pause the video,
open the transcript panel, scroll it to the end and read it. Same pacing as the end-screen read —
batches of about four, full navigation each time:

    document.querySelector('video')?.pause();
    const btn=[...document.querySelectorAll('button')]
      .find(b=>(b.getAttribute('aria-label')||'')==='Show transcript');
    if(btn)btn.click();
    let panel=null;
    for(let i=0;i<20;i++){
      await new Promise(r=>setTimeout(r,1000));
      panel=[...document.querySelectorAll('ytd-engagement-panel-section-list-renderer')]
        .find(p=>p.querySelector('transcript-segment-view-model, ytd-transcript-segment-renderer'));
      if(panel)break;
    }
    document.querySelector('video')?.pause();
    if(!panel)throw new Error('no transcript');
    const line=s=>{
      const ts=s.querySelector('.segment-timestamp, [class*="ViewModelTimestamp"]:not([class*="A11y"])');
      const tx=s.querySelector('.segment-text, span.ytAttributedStringHost');
      return ts&&tx?ts.innerText.trim()+' '+tx.innerText.replace(/\s+/g,' ').trim():null;
    };
    const sc=[...panel.querySelectorAll('*')].find(e=>e.scrollHeight>e.clientHeight+50);
    if(sc){for(let i=0;i<40;i++){
      sc.scrollTop=sc.scrollHeight;
      await new Promise(r=>setTimeout(r,250));
      if(sc.scrollTop+sc.clientHeight>=sc.scrollHeight-5&&i>2)break;}}
    const all=[...panel.querySelectorAll('transcript-segment-view-model, ytd-transcript-segment-renderer')]
      .map(line).filter(Boolean);
    ({v:new URL(location.href).searchParams.get('v'),n:all.length,tail:all.slice(-6).join('\n')})

Save the tail as `<work dir>/data/transcripts/<id>.txt`.

- **Two panels exist and both are live.** The older one renders `ytd-transcript-segment-renderer`,
  the newer one `transcript-segment-view-model` with different class names. YouTube serves either,
  sometimes to the same account on different videos, so match both.
- **Do not filter by the panel's `target-id`.** On the newer panel it is often `null`. Find the
  panel by the segments it contains.
- **The newer panel only renders what is on screen.** Without the scroll, you get the first
  fourteen lines and never see the ending — which is the only part that matters.
- **Return the tail, not the whole transcript.** The promise lives in the last minute or two, and
  a full transcript of every video buries everything else you are holding.
- The panel can take fifteen seconds or more to fill on a long video, so poll patiently.

Some videos have no transcript at all — captions turned off, or a members-only video. **Write no
file for those**, never an empty or invented one. `build_page.py` counts the videos whose outro
was never read and prints them; say the same thing to the creator, because those videos are in
the map but cannot be in the worklist.

Fetching the caption file directly does not work any more — YouTube's timedtext endpoint returns
an empty body without a token the page will not hand over. The panel is the way.

## Judge

    python3 <skill dir>/scripts/build_data.py --work DIR   # -> data/graph.json

`build_data.py` stops and prints the config snippet to add when a row names a video it cannot
find — an end screen pointing at another channel, or at a conference talk.

Now read the outros and write `<work dir>/data/actions.json` yourself. This is the part no script
can do. The schema is in `reference/actions.md`, and so are the rules for each bucket. Read it
before writing a line of JSON.

The short version:

- Read the **last ~90 seconds** of each transcript. That is where the promise lives, and the
  timestamps make the end easy to find.
- Quote what the outro actually says, verbatim. A paraphrase makes the finding unverifiable
  and the creator will not trust it.
- Every recommendation names a concrete destination video, chosen by the rules in
  `reference/actions.md`.

## Build

    python3 <skill dir>/scripts/build_page.py --work DIR

Writes `<work dir>/end-screen-audit.html` — one self-contained page, offline, light and dark,
thumbnails embedded. It also prints what the run left out. Read that, pass it on, and open the
page rather than just declaring it built.

If the creator wants it as a shareable link, publish `<work dir>/data/artifact.html` with the
Artifact tool. Keep the local file either way: an artifact URL dies without internet.

## Re-running later

After publishing a video or changing end screens in Studio, redo the Content read and the
export, then the Studio read for the videos that changed, and rebuild. The judgment in
`actions.json` is worth revisiting whenever a promised follow-up ships — that is exactly what
turns an item from "promise with nothing behind it" into "promise kept, end screen never
updated".
