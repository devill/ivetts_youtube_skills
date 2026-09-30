# Grouping and order

Read every transcript before grouping any take.
Do not decide from file names or from the first clip you open.
The creator usually recorded several attempts at each section.
Those attempts may share almost no words.

Group each take by what it is an attempt at.
Use the place, topic, scene, or story beat.
Do not group by matching words.
Do not use embeddings or an automatic clustering method.
Judgement is better here, and one wrong grouping poisons every later choice.
Treat a rephrased take as belonging to the same section when its purpose is the same.

Use the footage and its metadata as evidence.
Check filenames for camera date and time where they encode it.
Check recording dates.
Use location metadata when it exists.
GPS tracks from a watch, phone, or camera can connect takes to a place.
Use those clues to propose groups, not to settle them blindly.
A filename can be wrong or incomplete.
A familiar phrase can occur in several different story beats.
Read the surrounding material before deciding.

Build a proposed section list before the judging pass.
Give every section:

- A short stable key.
- A human label.
- One line explaining its job in the story.

Keep labels useful to a creator scanning `candidates.json`.
Do not hide uncertainty inside a vague label.
Mark a group that may contain two different beats and resolve it before judging.
Show the proposed list to the creator.
Get corrections before spending money or time on the judging pass.

Set the narrative order from the creator's intended story.
Use the journey there and back, an argument building, or a tour's path.
Do not use recording chronology as the default timeline.
Metadata proposes; the creator decides.
If the creator has not supplied an order, offer a clear proposal and ask for correction.
Reordering later is cheap: it is the order of the entries in `candidates.json`.
Re-judging every take later is not cheap.

When a section was recorded on several days, use the later day as a soft default.
Later takes are often more relaxed.
Never treat that as a rule.
A compelling earlier take can belong anywhere in the final story.
Mix recording days freely when the material works better that way.

Prefer fewer, longer takes.
Choose a take that covers a whole section over two half takes.
Allow one or two cuts inside spoken material when the section is otherwise strong.
Those cuts can be covered with B-roll in the real edit.
Treat a string of small speech cuts as evidence that the wrong take was chosen.
Do not assemble a section from fragments merely because each fragment sounds acceptable alone.

Record every section that has no usable take.
Write it as a content gap in `notes.md`.
A gap is a finding, not a failed run.
The creator may re-record it or cover it with B-roll.
Do not invent a candidate to make the JSON look complete.

Write sections to `candidates.json` in final narrative order.
Put candidates under the section they actually attempt.
Keep all surviving alternate phrasings under that section.
The order of the sections in this file is the order of the exported timeline.
Changing that order changes the rough cut.
Verify the order once more before exporting.
