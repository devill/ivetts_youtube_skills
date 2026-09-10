#!/usr/bin/env python3
"""Every upload on the authorised channel, with its lifetime public statistics."""
import json
from collections import Counter

from googleapiclient.discovery import build

from auth import data_path, load_credentials, resolve_work_dir, work_dir_parser


def own_channel(youtube):
    items = youtube.channels().list(part='snippet,contentDetails', mine=True).execute()['items']
    if not items:
        raise SystemExit('The authorised Google account has no YouTube channel.')
    return items[0]


def uploaded_video_ids(youtube, uploads_playlist):
    ids, token = [], None
    while True:
        response = youtube.playlistItems().list(
            part='contentDetails', playlistId=uploads_playlist,
            maxResults=50, pageToken=token).execute()
        ids += [item['contentDetails']['videoId'] for item in response['items']]
        token = response.get('nextPageToken')
        if not token:
            return ids


def details_for(youtube, video_ids):
    videos = []
    for chunk in (video_ids[i:i + 50] for i in range(0, len(video_ids), 50)):
        response = youtube.videos().list(
            part='snippet,status,statistics,contentDetails', id=','.join(chunk)).execute()
        for video in response['items']:
            videos.append({
                'id': video['id'],
                'title': video['snippet']['title'],
                'publishedAt': video['snippet']['publishedAt'],
                'privacy': video['status']['privacyStatus'],
                'duration': video['contentDetails']['duration'],
                'views': int(video['statistics'].get('viewCount', 0)),
                'likes': int(video['statistics'].get('likeCount', 0)),
                'comments': int(video['statistics'].get('commentCount', 0)),
            })
    return videos


def main():
    args = work_dir_parser(__doc__).parse_args()
    work_dir = resolve_work_dir(args.work)
    youtube = build('youtube', 'v3', credentials=load_credentials(work_dir))

    channel = own_channel(youtube)
    data_path(work_dir, 'channel.json').write_text(json.dumps({
        'id': channel['id'],
        'title': channel['snippet']['title'],
    }, indent=1))

    ids = uploaded_video_ids(youtube, channel['contentDetails']['relatedPlaylists']['uploads'])
    videos = details_for(youtube, ids)
    data_path(work_dir, 'videos.json').write_text(json.dumps(videos, indent=1))
    print(len(ids), 'in uploads;', len(videos), 'fetched')
    print(Counter(video['privacy'] for video in videos))


if __name__ == '__main__':
    main()
