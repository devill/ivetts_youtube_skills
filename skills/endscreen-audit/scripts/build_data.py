#!/usr/bin/env python3
"""One JSON the page can render: long-form public videos, their stats, their end-screen links.

Every fact comes from what the browser left in data/ — the Content page, the Shorts
tab, the end-screen reads and the Studio analytics export.

End-screen links come from YouTube Studio, not the public watch page: only Studio
distinguishes a link the creator pinned from an auto slot ("Best for viewer", "Most
recent upload") that YouTube fills differently for every viewer. Auto slots are dropped.
"""
import base64
import json
import re
import sys
import urllib.error
import urllib.request

from paths import data_path, load_json, resolve_work_dir, work_dir_parser
from studio_export import published_date, studio_rows

PRODUCED_BY = {
    'videos.json': 'Read every upload from the Studio Content page into it (step 1 of the '
                   'skill), then run select_videos.py.',
    'shorts.json': 'Read the ids under the Studio Shorts tab into it (step 1 of the skill), '
                   'then run select_videos.py.',
    'long_form.json': 'Run select_videos.py --work DIR first; it writes this file.',
    'studio_endscreens.json': "Read each long-form video's end screen in YouTube Studio into "
                              'it (step 3 of the skill), as {"<video id>": ["<row>", ...]}.',
}

HEADERS = {'User-Agent': 'Mozilla/5.0'}
BEST_FOR_VIEWER = 'Best for viewer'
MOST_RECENT = 'Most recent upload'
AUTO_SLOTS = {BEST_FOR_VIEWER, MOST_RECENT}


def required(work_dir, name):
    """A file an earlier step should have left behind, named with the step that leaves it."""
    return load_json(data_path(work_dir, name), PRODUCED_BY[name])


def videos_by_id(work_dir):
    """Studio's visibility word is what the page calls the video's privacy."""
    return {video['id']: {'id': video['id'], 'title': video['title'],
                          'privacy': video['visibility'].lower()}
            for video in required(work_dir, 'videos.json')}


def duration_of(row):
    seconds = row.get('Duration')
    return int(seconds) if seconds else None


def off_channel_targets(work_dir):
    config = work_dir / 'config.json'
    if not config.exists():
        return {}
    return load_json(config).get('offChannel', {})


def video_id_of(target):
    """A config entry may be a bare video id or the watch/youtu.be URL it was copied from."""
    match = re.search(r'(?:v=|youtu\.be/|/shorts/|/embed/)([\w-]{11})', target)
    return match.group(1) if match else target


def thumbnail_data_uri(video_id):
    for name in ('mqdefault.jpg', 'hqdefault.jpg', 'default.jpg'):
        url = f'https://i.ytimg.com/vi/{video_id}/{name}'
        try:
            raw = urllib.request.urlopen(
                urllib.request.Request(url, headers=HEADERS), timeout=30).read()
        except urllib.error.URLError:
            continue
        return 'data:image/jpeg;base64,' + base64.b64encode(raw).decode()
    return None


def number(text):
    return float(text) if text not in (None, '', 'NaN') else None


def titles_to_ids(videos, long_form):
    """Two uploads can share a title; the published one is what an end screen means."""
    def is_the_one_meant(video):
        return video['id'] in long_form, video['privacy'] == 'public'

    sharing_a_title = {}
    for video in videos.values():
        sharing_a_title.setdefault(video['title'], []).append(video)
    return {title: max(group, key=is_the_one_meant)['id']
            for title, group in sharing_a_title.items()}


def node_for(video, row, endscreen_rows):
    duration = duration_of(row)
    views = number(row.get('Views')) or 0
    watch_hours = number(row.get('Watch time (hours)')) or 0
    average_duration = watch_hours * 3600 / views if views else None
    average_percentage = (average_duration / duration * 100
                          if average_duration and duration else None)
    return {
        'id': video['id'],
        'title': video['title'],
        'published': published_date(row),
        'duration': duration,
        'thumbnail': thumbnail_data_uri(video['id']),
        'views': int(views),
        'impressions': int(number(row.get('Thumbnail impressions')) or 0),
        'clickThroughRate': number(row.get('Thumbnail click-through rate (%)')),
        'averageViewDuration': round(average_duration) if average_duration else None,
        'averageViewPercentage': average_percentage and round(average_percentage, 1),
        'bestForViewer': endscreen_rows.count('Video: ' + BEST_FOR_VIEWER),
        'mostRecentUpload': endscreen_rows.count('Video: ' + MOST_RECENT),
        'subscribeElement': any(r.startswith('Subscribe:') for r in endscreen_rows),
    }


def report_unmatched(work_dir, labels):
    snippet = json.dumps({'offChannel': {label: 'VIDEO_ID_OR_URL' for label in labels}},
                         indent=2, ensure_ascii=False)
    print(f'{len(labels)} end-screen target(s) match no video on this channel:', file=sys.stderr)
    for label in labels:
        print(f'  {label}', file=sys.stderr)
    print(f'\nThey link somewhere else — another channel, or a video that has since been '
          f'removed. Name each one in {work_dir / "config.json"}:\n\n{snippet}', file=sys.stderr)
    raise SystemExit(1)


def require_endscreens(long_form, endscreens):
    """Studio is read a tab at a time; a video missed there must not pass for one with no links."""
    missing = [video_id for video_id in long_form if video_id not in endscreens]
    if missing:
        raise SystemExit(
            f'{len(missing)} long-form video(s) are missing from studio_endscreens.json:\n'
            + '\n'.join(f'  {video_id}' for video_id in missing)
            + '\nRead those videos\' end screens in YouTube Studio and add them. A video with '
              'no end screen at all is written as an explicit [].'
        )


def build_edges(work_dir, long_form, endscreens, by_title):
    off_channel = off_channel_targets(work_dir)
    edges, unmatched = [], []
    for source in long_form:
        for row in endscreens[source]:
            kind, _, label = row.partition(': ')
            if kind == 'Video':
                if label in AUTO_SLOTS:
                    continue
                target = by_title.get(label)
                if target is None and label in off_channel:
                    target = video_id_of(off_channel[label])
                if target is None:
                    if label not in unmatched:
                        unmatched.append(label)
                    continue
            elif kind == 'Playlist':
                target = 'playlist:' + label
            else:
                continue
            edges.append({'from': source, 'to': target, 'label': label})
    if unmatched:
        report_unmatched(work_dir, unmatched)
    return edges


def outside_kind(target, videos, shorts):
    if target.startswith('playlist:'):
        return 'Playlist'
    video = videos.get(target)
    if video is None:
        return 'Other channel'
    return 'Short' if target in shorts else video['privacy'].capitalize()


def outside_node(target, label, videos, studio, shorts):
    row = studio.get(target, {})
    return {
        'id': target,
        'title': label,
        'outside': True,
        'kind': outside_kind(target, videos, shorts),
        'published': published_date(row),
        'duration': duration_of(row),
        'thumbnail': None if target.startswith('playlist:') else thumbnail_data_uri(target),
    }


def require_long_form(long_form):
    if not long_form:
        raise SystemExit(
            'data/long_form.json is empty, so there is nothing to build a map out of.\n'
            'select_videos.py found no published long-form video. Check that data/videos.json '
            'holds the whole Studio Content page, then run select_videos.py again.')


def main():
    args = work_dir_parser(__doc__).parse_args()
    work_dir = resolve_work_dir(args.work)
    videos = videos_by_id(work_dir)
    long_form = required(work_dir, 'long_form.json')
    require_long_form(long_form)
    shorts = set(required(work_dir, 'shorts.json'))
    endscreens = required(work_dir, 'studio_endscreens.json')
    studio = studio_rows(work_dir)
    require_endscreens(long_form, endscreens)

    # Edges first: an unmatched end-screen target then fails in a second, not after 40 downloads.
    edges = build_edges(work_dir, long_form, endscreens, titles_to_ids(videos, long_form))

    nodes = [node_for(videos[video_id], studio.get(video_id, {}), endscreens[video_id])
             for video_id in long_form]
    known = {node['id'] for node in nodes}

    outside = {}
    for edge in edges:
        label = edge.pop('label')
        edge['offChannel'] = edge['to'] not in known
        if edge['offChannel']:
            outside[edge['to']] = label

    nodes += [outside_node(target, label, videos, studio, shorts)
              for target, label in outside.items()]
    nodes.sort(key=lambda node: node['published'] or '9999')
    data_path(work_dir, 'graph.json').write_text(
        json.dumps({'nodes': nodes, 'edges': edges}, indent=1))
    print(len(nodes), 'nodes,', len(edges), 'edges')


if __name__ == '__main__':
    main()
