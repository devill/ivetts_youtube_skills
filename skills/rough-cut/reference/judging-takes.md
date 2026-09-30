# Judging takes

Use an audio-capable language model as a pre-selection filter.
Use Gemini, an OpenAI model, or a suitable local audio model when available.
Do not present its choices as the final edit.
The creator's taste decides between usable alternatives.

Start from `speech.json` for each clip.
Use its acoustic speech regions, not guessed text boundaries.
Split a region longer than about three minutes.
Cut it at the longest pauses you can find.
Number the resulting chunks per clip.
Tell the model the exact start offset of every chunk.
Keep the offset with the result so seconds can be mapped back to the clip.

Give the model a strict output contract.
For every cleanly delivered, complete-sentence attempt, require:

- The verbatim spoken text.
- The exact start time in seconds.
- The exact end time in seconds.
- A delivery confidence from 1 to 5.
- One short note about what is wrong or notable.

Ask for strict JSON and no surrounding commentary.
Keep every alternate phrasing of the same sentence.
The creator may prefer a less polished wording or a different mood.
Do not ask the model to choose one winner.
Do not let it discard a take merely because it differs from the script.

Treat these as potentially usable:

- Background wind, traffic, or activity.
- A small slip of the tongue when the mood is right.
- An accent.
- Dialogue that can be cleaned in the edit.

Treat these as disqualifying for the candidate list:

- A stuttered restart that never becomes a complete attempt.
- A half sentence.
- An answer with no question or context to make it stand alone.
- A take that ends mid-word.

Run a text-only quality pass after the audio pass.
Drop excerpts that are not standalone sentences or usable section attempts.
Keep this pass separate from audio judgement.
Text alone cannot tell you whether delivery was relaxed, hesitant, or convincing.

Verify every surviving span against segment timestamps.
Compare its text with the uncorrected transcript and its start and end with the real region.
Snap a slightly loose boundary to the real speech span.
Drop a span that cannot be matched to reality.
Models sometimes fabricate a plausible-looking time range.
Never allow a neat JSON result to overrule the footage.
Add the normal edit padding only when the export phase needs it.

Estimate paid use before sending audio.
Multiply the audio minutes by the model's audio rate.
Show the estimate to the creator and get approval before a paid API run.
Do not incur a cost on the assumption that approval is implied.
Afterwards report audio minutes, input and output tokens when available, and real cost.

Save each chunk result as a small JSON file under `judging/` in the work dir, named `<clip>.<chunk-start-seconds, 2dp>.json`. Clip names are file stems, so they are filesystem-safe. Do not discard results after combining them.
A failed later step must be resumable without paying for the same audio again.
Retry only missing or invalid chunks.

Write the surviving results to `candidates.json`.
Put sections in their intended narrative order.
Under each section, each candidate object must be exactly `{"clip","start","end","text","rating","note"}`.
Normalise every candidate identity as `clip|{float(start):.4f}`.
Keep usable but rejected options visible for the creator's workbench.
Do not include outright half-sentences merely to increase the list.

The model pre-selects; the creator judges.
Open the candidates in the workbench and let the creator watch them.
Keep audio in the loop whenever corrected text and delivery disagree.
