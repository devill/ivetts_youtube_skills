# Ivett's YouTube skills

Tools for YouTube creators that run inside **Claude Code** — Anthropic's assistant that works on
your own machine, with your own files and your own channel data. Nothing here is uploaded
anywhere.

You do not need to be a programmer. You do need to be willing to copy a few commands.

## Getting set up, once

1. Install Claude Code: <https://claude.com/claude-code>. Open it in a terminal.
2. Add this collection:

   ```
   /plugin marketplace add devill/ivetts_youtube_skills
   ```

3. Install the skill you want (below), then just ask for it in your own words.

---

## endscreen-audit

```
/plugin install endscreen-audit@ivetts-youtube-skills
```

Your back catalogue is traffic you already paid for. End screens are where it goes next — and
on most channels nobody has looked at them since the day each video went up.

This builds **one page** for your channel: a map of which published long-form video links to
which, with lifetime stats on hover, and a worklist of the repairs worth making, ordered so you
can do one a day.

Ask for it by name, or with *"where do my videos send people next?"*, *"audit my end screens"*,
or *"my old videos point at nothing"*.

### What it finds

It reads the last ninety seconds of every video's transcript — where the promise lives — and
compares what you said out loud with what the end screen actually does:

- **Promises with nothing behind them** — the outro names a follow-up that was never released,
  or points at a video viewers cannot watch.
- **Promises kept, end screen never updated** — the follow-up shipped months ago. The end
  screen still does not point at it. Cheapest wins on the channel.
- **Outros that fit any link** — nothing specific is promised, so the end screen can point
  anywhere without re-recording a second of audio.
- **Outros worth trimming** — a plug for an event that has passed, pinning the ending to a
  moment that is gone.
- **Thumbnails worth redoing** — low click-through rate, healthy watch time. People who click
  stay, so the packaging is what costs the views. Outliers are deliberately excluded: a video
  pushed far outside your audience has a low CTR because strangers scrolled past it, not
  because the thumbnail is bad.

Every recommendation names a concrete destination, picked from the recent videos that hold
attention once someone arrives — and never a video that repeats what the viewer just watched in
a slightly newer or older version.

### Why it reads Studio and not the watch page

The public watch page resolves *Best for viewer* and *Most recent upload* into concrete videos,
differently for every viewer. Scrape that and the map invents links you never made. Only the
Studio editor tells a link you pinned from a slot YouTube fills. So the end-screen read drives
a real browser through Studio; everything else comes from the YouTube Data and Analytics APIs
with your own credentials.

One thing no API will give you: click-through rate. Thumbnail impressions and CTR exist only in
the Studio CSV export, so the skill asks you to export it once, by hand.

### What you need

- A Google Cloud OAuth **Desktop app** client, with YouTube Data API v3 and YouTube Analytics
  API enabled. The skill walks you through creating one; it stays on your machine and gives the
  tool read access to your own channel only.
- One `Table data.csv` lifetime export from YouTube Studio.
- A Studio tab left visible on screen while the end screens are read — Chrome will not render
  the video editor in a hidden tab.

The finished page is a single self-contained HTML file: offline, light and dark, thumbnails
embedded. Publish it as a shareable link if you want one, but the file is yours either way.

---

Not a developer tool. If you write code, the rest of my Claude Code skills live in
[devill/ivetts-skills](https://github.com/devill/ivetts-skills).

