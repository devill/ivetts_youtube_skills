#!/usr/bin/env python3
"""The videos the audit is about: public, long-form, oldest upload first.

Writes data/long_form.json, the list of ids every later step works through —
including the browser reads of end screens and transcripts, which need to know
which videos to visit. A video published too recently to appear in the Studio
export is still one of them; it just has no numbers yet.
"""
import json

from paths import data_path, load_json, resolve_work_dir, work_dir_parser
from studio_export import published_date, studio_rows

PUBLIC = 'public'

VISIBILITY_WORDS = {PUBLIC, 'private', 'unlisted', 'scheduled', 'draft'}

BROWSER_READS = {
    'videos.json': 'every upload from the Studio Content page, as '
                   '[{"id": ..., "title": ..., "visibility": ...}]',
    'shorts.json': 'the video ids listed under the Studio Shorts tab, as [...]',
}

READ_CONTENT_AGAIN = ('Read the Studio Content page again into data/videos.json, paging with the '
                      'arrow at the bottom until it stops.')


def require_browser_read(work_dir, name):
    path = data_path(work_dir, name)
    if not path.exists():
        raise SystemExit(f'No {path}.\nRead {BROWSER_READS[name]} in YouTube Studio '
                         'and save it there before running this.')
    return load_json(path)


def visibility_word(video):
    """Studio writes "Public" or "Public Made for kids"; the first word is the visibility."""
    words = str(video.get('visibility') or '').split()
    return words[0].lower() if words else ''


def require_english_visibility(uploads):
    """Every later step trusts this word to tell a published video from a hidden one."""
    unrecognised = sorted({str(video.get('visibility')) for video in uploads
                           if visibility_word(video) not in VISIBILITY_WORDS})
    if not unrecognised:
        return
    raise SystemExit(
        f'{len(unrecognised)} of the visibility words in data/videos.json are not ones this '
        'audit recognises, for example:\n'
        + '\n'.join(f'  {word}' for word in unrecognised[:3])
        + '\n\nIt expects Studio\'s own English words: Public, Private, Unlisted, Scheduled, '
          'Draft. Without them there is no way to tell a published video from a hidden one, so '
          'the audit would be about the wrong videos.\n\nSwitch YouTube Studio to English (the '
          f'gear at the bottom of the left menu -> Language). {READ_CONTENT_AGAIN}')


def unique_uploads(videos):
    """Studio's Content page is read a page at a time; a row seen twice is one video."""
    by_id = {}
    for video in videos:
        by_id.setdefault(video['id'], video)
    return list(by_id.values())


def public_long_form(uploads, shorts):
    return [video['id'] for video in uploads
            if visibility_word(video) == PUBLIC and video['id'] not in shorts]


def require_selection(long_form, uploads, shorts):
    if long_form:
        return
    raise SystemExit(
        f'None of the {len(uploads)} uploads in data/videos.json is a published long-form '
        f'video, so there is nothing to audit ({len(shorts)} of them are Shorts, the rest are '
        'not Public).\nThe likeliest cause is that data/videos.json holds only part of the '
        f'Content page — the Shorts tab alone, or one page of it. {READ_CONTENT_AGAIN}')


def report_not_in_content(studio, uploads):
    """The Content page is read a page at a time, so the export can know a video it missed."""
    known = {video['id'] for video in uploads}
    unread = [video_id for video_id in studio if video_id not in known]
    if not unread:
        return
    print(f'Checked: the Studio export holds {len(unread)} video(s) that data/videos.json '
          f'does not, out of {len(studio)} —', ', '.join(unread))
    print('  One or two are normally videos deleted since the export. Many would mean the '
          'Content page was not paged to the end.')


def main():
    args = work_dir_parser(__doc__).parse_args()
    work_dir = resolve_work_dir(args.work)
    uploads = unique_uploads(require_browser_read(work_dir, 'videos.json'))
    require_english_visibility(uploads)
    shorts = set(require_browser_read(work_dir, 'shorts.json'))
    studio = studio_rows(work_dir)

    long_form = public_long_form(uploads, shorts)
    require_selection(long_form, uploads, shorts)
    long_form.sort(key=lambda video_id: published_date(studio.get(video_id, {})) or '9999')
    data_path(work_dir, 'long_form.json').write_text(json.dumps(long_form, indent=1))

    unmeasured = [video_id for video_id in long_form if video_id not in studio]
    print(len(uploads), 'uploads;', len(shorts), 'Shorts;', len(long_form), 'long-form,',
          len(unmeasured), 'of them with no numbers yet')
    report_not_in_content(studio, uploads)


if __name__ == '__main__':
    main()
