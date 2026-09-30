# Transcription

Create one plain-text source transcript for every clip in scope.

- Make `transcripts/<clip>.txt`.
- Remove only the clip's extension when choosing the file name.
- Keep the original transcript for the life of the work folder.
- Never edit it in place.
- Never delete it to save space.
- Treat it as an expensive source file, not as disposable working text.

Choose the speech-to-text tool already installed on the machine.
Do not make the creator install a package before checking what is available.
Before any batch run, run the chosen tool's `--help` (or equivalent) and transcribe exactly ONE clip first; verify the output file actually landed in `transcripts/` with the expected name. Tools differ in output naming, and faster-whisper is a Python API with no CLI at all. Only then batch the rest.
Use whichever shape fits the installation:

```sh
whisper CLIP.mp4 --language hu --output_format txt --output_dir transcripts/
```

```sh
whisper.cpp -m models/ggml-small.bin -f CLIP.wav \
  -l hu -otxt -of transcripts/CLIP
```

```sh
faster-whisper CLIP.mp4 --language hu --output_dir transcripts/
```

For an MLX command, pass the equivalent explicit language option:

```sh
mlx-whisper CLIP.mp4 --language hu --output-format txt --output-dir transcripts/
```

Use the real language code for the footage.
Do not rely on automatic language detection when the language is known.
An explicit language reduces wrong vocabulary and wasted model guesses.

Ask for plain text in every run.
Also ask for JSON, VTT, SRT, or another segment format when the tool supports it.
Keep that timestamped file beside the plain text only when the tool verifiably writes it next to the `.txt` with a predictable name. If it does not, proceed with `.txt` only and get timestamps from the judging pass instead of improvising output flags mid-batch.
Segment timestamps are needed to find candidate takes.
They are also needed to verify every later cut point.
Do not replace the plain text with a timestamped format.

Pick the model size as a trade-off, not as a test of perfection.
Small models finish sooner but garble more words.
Larger models cost more time and memory and may still miss names.
The transcript only needs to find and judge sections.
Fix misheard words in the transcript-fixing phase.
Do not rerun the whole batch just because a proper noun is wrong.

Batch the entire folder in one unattended run.
Start every clip in scope, not only the clip that looks easiest.
This is the slow phase: expect roughly real time per clip, and longer on a CPU.
Long clips and many clips are normal.
Start the run and let it finish rather than repeatedly checking each file.
Record failures and continue with the other clips where the tool permits it.
Retry a failed clip after the batch, without overwriting a successful source file.

Check that every input has one matching `.txt` output.
Check that timestamped output exists where the chosen tool promised it.
Open a sample from the beginning, middle, and end of the batch.
Confirm that the language is plausible and that timestamps increase.
Do not silently accept an empty or truncated file.

Expect proper nouns to be wrong.
Foreign place names, product names, lift names, streets, and people are especially fragile.
A German lift name may become convincing nonsense in a Hungarian transcript.
Keep the nonsense in the original source file for traceability.
Correct it later with a script or a small gazetteer.

Remember what the transcript cannot tell you.
Speech recognition often removes false starts and stutters from the text.
It can make a hesitant delivery read clean and fluent.
Never treat it as a record of how the creator spoke.
Choose takes from audio, or from audio checked against the uncorrected transcript.

Finish by recording the files made and any clips that failed.
Leave the source transcripts ready for grouping, fixing, and timestamp verification.
