# Ivett's YouTube skills

Tools for YouTube creators that run inside **Claude Code** — Anthropic's assistant that works on
your own machine, in your own browser, with your own channel. Nothing is stored on anyone else's
server.

You do not need to be a programmer. You copy two commands once, and after that you ask for
things in plain English.

## Setting up, once

1. Install Claude Code: <https://claude.com/claude-code>. Open it in a terminal.
2. Add this collection:

   ```
   /plugin marketplace add devill/ivetts_youtube_skills
   ```

3. Install the skill you want, below.

You also need Python 3, which every Mac and most Linux machines already have. Type `python3
--version` in the terminal; if it answers with a number you are set, and if it does not, Claude
will tell you how to get it.

---

## endscreen-audit

```
/plugin install endscreen-audit@ivetts-youtube-skills
```

Your back catalogue is traffic you have already paid for. End screens decide where it goes next
— and on most channels nobody has looked at them since the day each video went up.

Ask for it by name, or with *"where do my videos send people next?"*, *"audit my end screens"*,
or *"my old videos point at nothing"*.

You get one page. A map of which of your videos links to which, with lifetime stats on hover,
and a worklist of the repairs worth making, ordered so you can do one a day.

### What it finds

It reads the last ninety seconds of every video's transcript — where you make your promise —
and compares what you said out loud with where the end screen actually sends people:

- **Promises with nothing behind them.** The outro names a follow-up you never released, or
  points at a video viewers cannot watch.
- **Promises you kept, end screens you forgot.** The follow-up shipped months ago and the end
  screen still ignores it. Cheapest wins you have.
- **Outros that fit any link.** Nothing specific is promised, so you can point that end screen
  anywhere without re-recording a second of audio.
- **Outros worth trimming.** A plug for an event that has passed, holding the ending hostage to
  a moment that is gone.
- **Thumbnails worth redoing.** Low click-through, healthy watch time: people who click stay, so
  the packaging is what is costing you views.

Every suggestion names a specific video to point at — one of the recent ones that hold attention
once someone arrives, and never one that repeats what the viewer has just watched.

Your outliers are left alone. A video that reached far outside your audience has a low
click-through rate because strangers scrolled past it, not because the thumbnail is bad, and
repackaging it chases people who were never yours.

### What you do

Sign in to YouTube Studio in Chrome, set it to English, and leave the window on screen. Claude
reads your channel through it: your video list, your end screens, and each video's transcript.
One step is yours: Claude sets up the lifetime analytics export and then asks you to press the
download button, because Chrome refuses downloads that software starts. That export is the only
place YouTube puts click-through rate.

A video with captions turned off has no transcript to read, so its outro cannot be checked.
Claude tells you which ones those were.

Then leave it alone for a while. It visits every published video, so a fifty-video channel is
not a two-minute job.

### What you get back

A single HTML file. It works offline, it follows your light or dark theme, and the thumbnails
are baked into it, so you can keep it, mail it, or open it in a year. Ask and Claude will
publish it as a link as well.
