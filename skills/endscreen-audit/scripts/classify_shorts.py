#!/usr/bin/env python3
"""Tell Shorts from long-form: /shorts/<id> stays put for a Short, redirects otherwise.

Writes data/is_short.json (every public upload) and data/long_form.json (the
public non-Shorts, which the later scripts work through).
"""
import json
import random
import time
import urllib.request

from auth import data_path, load_json, resolve_work_dir, work_dir_parser

# Without a consent cookie the EU consent wall redirects every request, which
# would otherwise read as "not a Short" for the whole channel.
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36',
           'Cookie': 'SOCS=CAISEwgDEgk2NzI4NDMyMzQaAmVuIAEaBgiA_LyaBg'}


class KeepRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args):
        return None


opener = urllib.request.build_opener(KeepRedirect)


def is_short(video_id):
    request = urllib.request.Request(f'https://www.youtube.com/shorts/{video_id}', headers=HEADERS)
    try:
        return opener.open(request, timeout=30).status == 200
    except urllib.error.HTTPError as error:
        if error.code in (301, 302, 303, 307, 308):
            return False
        raise


def public_videos(work_dir):
    seen, videos = set(), []
    for video in load_json(data_path(work_dir, 'videos.json')):
        if video['privacy'] == 'public' and video['id'] not in seen:
            seen.add(video['id'])
            videos.append(video)
    return videos


def main():
    args = work_dir_parser(__doc__).parse_args()
    work_dir = resolve_work_dir(args.work)
    store = data_path(work_dir, 'is_short.json')
    videos = public_videos(work_dir)
    known = load_json(store) if store.exists() else {}
    for video in videos:
        if video['id'] in known:
            continue
        for attempt in range(6):
            try:
                known[video['id']] = is_short(video['id'])
                break
            except Exception as error:
                print('retry', video['id'], error, flush=True)
                time.sleep(15 * (attempt + 1))
        else:
            raise SystemExit(f'{video["id"]}: still unreadable after 6 attempts. '
                             'Left unclassified rather than guessed at — re-run when '
                             'YouTube is reachable again.')
        store.write_text(json.dumps(known, indent=1))
        time.sleep(random.uniform(1.0, 2.0))
    store.write_text(json.dumps(known, indent=1))

    long_form = [v['id'] for v in videos if not known.get(v['id'], False)]
    data_path(work_dir, 'long_form.json').write_text(json.dumps(long_form, indent=1))
    print('shorts', sum(known.values()), 'of', len(known), '; long-form', len(long_form))


if __name__ == '__main__':
    main()
