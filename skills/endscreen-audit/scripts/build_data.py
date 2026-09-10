#!/usr/bin/env python3
"""One JSON the page can render: long-form public videos, their stats, their end-screen links.

End-screen links come from YouTube Studio, not the public watch page: only Studio
distinguishes a link the creator pinned from an auto slot ("Best for viewer", "Most
recent upload") that YouTube fills differently for every viewer. Auto slots are dropped.
"""
import base64
import csv
import json
import re
import sys
import urllib.request

from auth import data_path, load_json, resolve_work_dir, work_dir_parser

HEADERS = {'User-Agent': 'Mozilla/5.0'}
BEST_FOR_VIEWER = 'Best for viewer'
MOST_RECENT = 'Most recent upload'
AUTO_SLOTS = {BEST_FOR_VIEWER, MOST_RECENT}

CSV_EXPORT_HELP = (
    'In YouTube Studio: Analytics -> Advanced mode -> date range Lifetime -> '
    'Content tab -> Export current view -> Comma-separated values (.csv), then '
    'unzip it and put "Table data.csv" there. It is the only source of '
    'thumbnail impressions and click-through rate.'
)


def seconds(iso):
    hours, minutes, secs = (int(x or 0) for x in
                            re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso).groups())
    return hours * 3600 + minutes * 60 + secs


def studio_rows(work_dir):
    table = data_path(work_dir, 'csv', 'Table data.csv')
    if not table.exists():
        raise SystemExit(f'No YouTube Studio export at {table}.\n{CSV_EXPORT_HELP}')
    return {row['Content'].strip(): row for row in csv.DictReader(table.open())
            if row['Content'].strip() != 'Total'}


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
    by_title = {}
    for video in sorted(videos.values(),
                        key=lambda v: (v['id'] in long_form, v['privacy'] == 'public')):
        by_title[video['title']] = video['id']
    return by_title


def node_for(video, row, measured, endscreen_rows):
    duration = seconds(video['duration'])
    views = number(row.get('Views')) or 0
    watch_hours = number(row.get('Watch time (hours)')) or 0
    average_duration = measured.get('averageViewDuration')
    if average_duration is None and views:
        average_duration = watch_hours * 3600 / views
    average_percentage = measured.get('averageViewPercentage')
    if average_percentage is None and average_duration and duration:
        average_percentage = average_duration / duration * 100
    return {
        'id': video['id'],
        'title': video['title'],
        'published': video['publishedAt'][:10],
        'duration': duration,
        'thumbnail': thumbnail_data_uri(video['id']),
        'engagedViews': measured.get('engagedViews'),
        'views': int(views),
        'impressions': int(number(row.get('Thumbnail impressions')) or 0),
        'clickThroughRate': number(row.get('Thumbnail click-through rate (%)')),
        'averageViewDuration': average_duration and round(average_duration),
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


def outside_node(target, label, videos):
    published = videos.get(target)
    return {
        'id': target,
        'title': label,
        'outside': True,
        'kind': ('Playlist' if target.startswith('playlist:') else
                 'Other channel' if not published else
                 'Short' if published['privacy'] == 'public' else
                 published['privacy'].capitalize()),
        'published': published['publishedAt'][:10] if published else None,
        'duration': seconds(published['duration']) if published else None,
        'thumbnail': None if target.startswith('playlist:') else thumbnail_data_uri(target),
    }


def main():
    args = work_dir_parser(__doc__).parse_args()
    work_dir = resolve_work_dir(args.work)
    videos = {v['id']: v for v in load_json(data_path(work_dir, 'videos.json'))}
    long_form = load_json(data_path(work_dir, 'long_form.json'))
    endscreens = load_json(data_path(work_dir, 'studio_endscreens.json'))
    analytics = load_json(data_path(work_dir, 'analytics.json'))
    studio = studio_rows(work_dir)
    require_endscreens(long_form, endscreens)

    nodes = [node_for(videos[video_id], studio.get(video_id, {}),
                      analytics.get(video_id, {}), endscreens[video_id])
             for video_id in long_form]
    known = {node['id'] for node in nodes}

    edges = build_edges(work_dir, long_form, endscreens, titles_to_ids(videos, long_form))
    outside = {}
    for edge in edges:
        label = edge.pop('label')
        edge['offChannel'] = edge['to'] not in known
        if edge['offChannel']:
            outside[edge['to']] = label

    nodes += [outside_node(target, label, videos) for target, label in outside.items()]
    nodes.sort(key=lambda node: node['published'] or '9999')
    data_path(work_dir, 'graph.json').write_text(
        json.dumps({'nodes': nodes, 'edges': edges}, indent=1))
    print(len(nodes), 'nodes,', len(edges), 'edges')


if __name__ == '__main__':
    main()
