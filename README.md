# Ivett's YouTube skills

Tools for YouTube creators that run inside **pi** — a coding agent that works on your own
machine, in your own browser, with your own channel. Nothing is stored on anyone else's server.

You do not need to be a programmer. You copy a few commands once, and after that you ask for
things in plain English.

## Setting up, once

1. Install pi. You need Node.js first: type `npm --version` in a terminal; if it answers with a
   number you have it, and if not, the installer at <https://nodejs.org> is two clicks. Then:

   ```
   npm install -g --ignore-scripts @earendil-works/pi-coding-agent
   ```

2. Get the AI that powers it. These skills recommend **OpenCode Go**: a $10/month subscription
   with generous limits, and pi is one of the clients it officially supports. Subscribe at
   <https://opencode.ai/go>, copy your API key, then paste this into a terminal with your key in
   place of `PASTE-YOUR-KEY`:

   ```
   echo '{"opencode-go": {"type": "api_key", "key": "PASTE-YOUR-KEY"}}' > ~/.pi/agent/auth.json
   ```

3. Install this collection of skills:

   ```
   pi install git:github.com/devill/ivetts_youtube_skills
   ```

4. Start `pi` in any folder and ask for a skill by name. The first time, pi asks whether to trust
   the folder; say yes.

You also need Python 3, which every Mac and most Linux machines already have. Type `python3
--version` in the terminal; if it answers with a number you are set, and if it does not, your
agent will tell you how to get it.

---

## endscreen-audit

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

Sign in to YouTube Studio in Chrome, set it to English, and leave the window on screen. The agent
reads your channel through it: your video list, your end screens, and each video's transcript.
One step is yours: the agent sets up the lifetime analytics export and then asks you to press the
download button, because Chrome refuses downloads that software starts. That export is the only
place YouTube puts click-through rate.

A video with captions turned off has no transcript to read, so its outro cannot be checked. The
agent tells you which ones those were.

Then leave it alone for a while. It visits every published video, so a fifty-video channel is
not a two-minute job.

### What you get back

A single HTML file. It works offline, it follows your light or dark theme, and the thumbnails
are baked into it, so you can keep it, mail it, or open it in a year. Ask and your agent will
publish it as a link as well.

---

## rough-cut

You recorded the same part of your video three, four, five times, and now there are hours of
takes and no edit. Turning that folder into a first timeline by hand is an evening of scrubbing.
This skill does the boring parts and leaves the choices with you.

Ask for it by name, or with *"turn my footage into a rough cut"*, *"transcribe my takes and pick
the best ones"*, *"I recorded everything twice, help me choose"*, or *"make me an A-roll
string-out"*.

### What it does

The agent transcribes every clip, finds where you actually speak, groups the takes into the sections
of your video, and listens for the attempts where you delivered the whole thing cleanly. What it
thinks might work lands in a simple page: each attempt with its words, a play button, and three
buttons — use it, maybe, or reject it. You watch, you click, you type notes if something bothers
you. Everything saves as you go.

When you are done, the agent writes a timeline file. Premiere Pro, Final Cut Pro and DaVinci Resolve
each get the dialect they understand, your sections already in the order you said the video
should go, and the takes you maybe'd kept on the timeline but switched off, so flipping one is a
click in your editor.

A few things it refuses to get wrong, learned from real edits: your transcripts are kept forever,
because re-transcribing costs hours; a transcript that reads clean can hide that you stuttered,
so takes are judged by ear, never by text alone; and the last word of every take gets a little
extra room, because speech recognition is always in a hurry at the end of a sentence.

### What you do

Tell the agent where the footage is, what language you speak in it, and — if you recorded from a
teleprompter — where the script is. Say which editor you cut in. If you already know the order
the video should tell its story in, say so; if you don't, the agent proposes one from the material
and you correct it.

Then mark your takes. That part is yours, because which take is best is taste: a take with wind
noise and the right energy beats a technically perfect read that has none.

If the agent uses a paid AI service to listen through your takes, it tells you the rough cost first
and waits for your go-ahead.

### What you get back

A folder with your transcripts, the speech map, your marks, and the timeline files — plus a
`notes.md` so you can pick this up in a fresh session months later without starting over.
