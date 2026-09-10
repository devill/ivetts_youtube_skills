#!/usr/bin/env python3
"""Lifetime engaged views, average view duration and percentage, per video."""
import datetime
import json

from googleapiclient.discovery import build

from auth import data_path, load_credentials, load_json, resolve_work_dir, work_dir_parser

METRICS = 'engagedViews,averageViewDuration,averageViewPercentage'
EARLIEST_YOUTUBE_UPLOAD = '2005-01-01'


def channel_start(work_dir):
    published = [video['publishedAt'][:10]
                 for video in load_json(data_path(work_dir, 'videos.json'))]
    return min(published, default=EARLIEST_YOUTUBE_UPLOAD)


def rows_for(analytics, video_ids, start_date):
    response = analytics.reports().query(
        ids='channel==MINE',
        startDate=start_date,
        endDate=datetime.date.today().isoformat(),
        metrics=METRICS,
        dimensions='video',
        filters='video==' + ','.join(video_ids),
        maxResults=200,
    ).execute()
    columns = [column['name'] for column in response['columnHeaders']]
    return [dict(zip(columns, row)) for row in response.get('rows', [])]


def main():
    args = work_dir_parser(__doc__).parse_args()
    work_dir = resolve_work_dir(args.work)
    wanted = load_json(data_path(work_dir, 'long_form.json'))
    start_date = channel_start(work_dir)
    analytics = build('youtubeAnalytics', 'v2', credentials=load_credentials(work_dir))
    stats = {}
    for chunk in (wanted[i:i + 200] for i in range(0, len(wanted), 200)):
        for row in rows_for(analytics, chunk, start_date):
            stats[row.pop('video')] = row
    data_path(work_dir, 'analytics.json').write_text(json.dumps(stats, indent=1))
    print(len(stats), 'videos with analytics;', len(wanted), 'requested')


if __name__ == '__main__':
    main()
