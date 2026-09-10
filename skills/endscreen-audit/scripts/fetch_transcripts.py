#!/usr/bin/env python3
"""Download one caption track per long-form video, preferring uploaded tracks over ASR."""
import re

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from auth import data_path, load_credentials, load_json, resolve_work_dir, work_dir_parser


def best_track(tracks):
    def rank(track):
        snippet = track['snippet']
        return (snippet['trackKind'] != 'ASR', snippet['language'].startswith('en'))
    ready = [track for track in tracks if not track['snippet'].get('isDraft')]
    return max(ready, key=rank) if ready else None


def plain_text(srt):
    lines = []
    for block in srt.decode('utf8', 'ignore').split('\n\n'):
        rows = [row for row in block.strip().splitlines()
                if row and not row.isdigit() and '-->' not in row]
        if rows:
            lines.append(' '.join(rows))
    return re.sub(r'\s+', ' ', ' '.join(lines)).strip()


def main():
    args = work_dir_parser(__doc__).parse_args()
    work_dir = resolve_work_dir(args.work)
    out = data_path(work_dir, 'transcripts')
    out.mkdir(exist_ok=True)
    youtube = build('youtube', 'v3', credentials=load_credentials(work_dir))
    for video_id in load_json(data_path(work_dir, 'long_form.json')):
        target = out / f'{video_id}.txt'
        if target.exists():
            continue
        tracks = youtube.captions().list(part='snippet', videoId=video_id).execute()['items']
        track = best_track(tracks)
        if track is None:
            print('no caption track', video_id, flush=True)
            continue
        try:
            srt = youtube.captions().download(id=track['id'], tfmt='srt').execute()
        except HttpError as refused:
            # A third-party contributed track cannot be downloaded even by the
            # channel owner; YouTube answers 403 and the rest still works.
            if refused.resp.status != 403:
                raise
            print('download forbidden', video_id, flush=True)
            continue
        target.write_text(plain_text(srt))
        print(video_id, track['snippet']['trackKind'], len(target.read_text()), flush=True)


if __name__ == '__main__':
    main()
