# Transcription

Create one plain-text source transcript for every clip in scope.

- Make `transcripts/<clip>.txt`.
- Remove only the clip's extension when choosing the file name.
- Keep the original transcript for the life of the work folder.
- Never edit it in place.
- Never delete it to save space.
- Treat it as an expensive source file, not as disposable working text.

## Preferred: a subagent with audio input

A model with audio input is the transcriber of record when one is available.
It transcribes what was actually said — false starts, stutters, restarts and repeats included.
Whisper does not: it silently deletes them from the text, which is exactly the information the
edit needs.
In a real edit, a Gemini Flash subagent heard four false starts at the top of an intro that
Whisper had erased; `gemini-flash-latest` is the model alias that worked (the numbered
`gemini-2.5-flash` name returned 404 for a new account). An OpenAI audio model or a local audio
model are equivalent choices.

How to run it:

- Transcribe per speech region from `speech.json`, not the whole clip at once — the regions
  already exclude silence, which is most of the footage.
- Ask for strict JSON per region: verbatim text (false starts and stutters kept, no cleanup), and
  a start and end offset in seconds for every sentence attempt inside the region.
- Cap each request at a few minutes of audio; split longer regions at their longest pauses.
- State the cost (audio minutes × the model's rate) and get the go-ahead before a paid API; report
  the real numbers afterwards. Transcribing only the speech regions keeps this small.
- Save each region's result under `judging/` in the work dir, named
  `<clip>.<region-start-seconds, 2dp>.json`, so a failure resumes without re-paying.

Verify the first region before batching: read it against a moment of the actual audio, confirm the
offsets map back onto the clip, and confirm the false starts survived. Only then run the rest.

## Fallback: Whisper

When there is no audio-capable model, or the footage must stay free and local, use what is
installed — the `whisper` CLI, whisper.cpp, faster-whisper (a Python API with no CLI), or an MLX
variant. Do not make the creator install anything before checking.

Before any batch run, run the chosen tool's `--help` and transcribe exactly ONE clip first.
Verify the output actually landed in `transcripts/` with the expected name; tools differ in output
naming, and some write extra sidecar files. Only then batch the rest.

```sh
whisper CLIP.mp4 --language hu --output_format txt --output_dir transcripts/
```

```sh
whisper.cpp -m models/ggml-small.bin -f CLIP.wav \
  -l hu -otxt -of transcripts/CLIP
```

For an MLX command, pass the equivalent explicit language option:

```sh
mlx-whisper CLIP.mp4 --language hu --output-format txt --output-dir transcripts/
```

Use the real language code for the footage.
Do not rely on automatic language detection when the language is known.
An explicit language reduces wrong vocabulary and wasted model guesses.

Keep a timestamped sidecar (JSON, VTT, SRT) beside the plain text only when the tool verifiably
writes it with a predictable name. If it does not, proceed with `.txt` only — the timestamps come
from the audio-judging pass later.

Pick the model size as a trade-off, not as a test of perfection.
Small models finish sooner but garble more words.
The transcript only needs to find and judge sections; fix misheard words in the transcript-fixing
phase rather than rerunning the batch over a wrong proper noun.

Batch the entire folder in one unattended run — this is the slow phase, roughly real time per
clip and longer on a CPU. Record failures, continue, and retry a failed clip after the batch
without overwriting a successful source file.

Check that every input has one matching `.txt` output.
Open a sample from the beginning, middle and end of the batch.
Confirm the language is plausible and timestamps increase.
Do not silently accept an empty or truncated file.

## Either way

Expect proper nouns to be wrong.
Foreign place names, product names, streets and people are especially fragile.
A German lift name may become convincing nonsense in a Hungarian transcript.
Keep the nonsense in the original source file for traceability; correct it later with a gazetteer.

Remember what a machine transcript cannot tell you.
Whisper makes a hesitant delivery read clean and fluent; even an audio model asked to clean up
will smooth words if you let it — so always ask for verbatim.
Never treat transcript text as a record of how the creator spoke.
Choose takes from audio, or from audio checked against the uncorrected transcript.

Finish by recording the files made, the model or tool used, any clips that failed, and the cost if
a paid API ran.
Leave the source transcripts ready for grouping, fixing, and timestamp verification.
