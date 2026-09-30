# Transcript fixing

Fix a transcript only when a supplied script or known names make the correction reliable.
Write `<clip>.fixed.txt` beside the original.
Leave the original byte-for-byte unchanged.

Use this phase when the creator supplied teleprompter text.
Also use it when the topic has proper nouns that speech recognition is likely to miss.
Do not polish the transcript into a readable script.
Its structure carries timing meaning for the edit.
Each line or segment maps to real audio.

Preserve the segment structure exactly.
Never move words between segments.
Never delete stutters, restarts, repetitions, or filler words.
Keep noise and chatter lines, even when they look irrelevant.
Keep every timecode line exactly as supplied.
Change only words and marks that recognition got wrong.

Work segment by segment and take by take.
A line can contain several attempts at one sentence.
Some attempts will be aborted halfway through.
For each attempt, find the script sentence it is trying to say.
Compare them word by word and mark by mark.
Read for difference, not for sense.
A sentence that reads well can still contain a missing small word.

Classify every difference before changing it:

- Fix a recognition error.
- Leave a genuine rewording alone.
- Leave an aborted restart's words in place.
- Fix the punctuation of an aborted restart when the marks are wrong.

Use the script's punctuation as the authority.
If the script has a comma, join a false full-stop split and lowercase the continuation.
If the script has a full stop or ellipsis, keep the split.
Give a restart a full stop before it and a capital after it, even mid-line.
Check every segment boundary for a sentence that continues into the next segment.
Do not invent a pause merely because a line ends.

Correct common recognition errors carefully.

- Fix similar-sounding substitutions, including names.
- Restore dropped small words such as “the”, “a”, “we”, and “our”.
- Restore punctuation that changes a false split into the intended sentence.
- Keep wording that differs from the script when the speaker genuinely rephrased it.

Do not overrule the script by judging how similar two words sound.
If the script has a word there and the change is not plainly deliberate, use the script's word.
The speaker's deliberate rewording is the exception.
Do not turn that exception into a licence to rewrite delivery.

When there is no script, build a small gazetteer first.
List the real places, people, products, lifts, streets, and tools being discussed.
Ask the creator for names you cannot establish.
Search the topic's names when that is appropriate.
Fix against the gazetteer, not against what sounds plausible.
Report anything you cannot recover.
Never guess a proper noun and present it as fact.

Verify the finished file before handing it on.
Diff the timecode lines in the original and fixed files.
The diff must be empty.
Check that segment count and order are unchanged.
Report each file's fixes and the words deliberately left alone.

Remember that corrected words hide delivery problems.
A heavily corrected take may still be a stuttered take.
Never use the fixed transcript to judge delivery.
Use the audio or the untouched transcript for that judgement.
