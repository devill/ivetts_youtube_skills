#!/usr/bin/env python3
"""The one file YouTube Studio itself writes: the lifetime analytics export.

Both select_videos.py and build_data.py read it, and both need the same two
things — the rows keyed by video id, and Studio's publish date turned into a
date a computer can sort. Its column names and its dates are English UI text,
so a Studio set to another language produces a file this cannot read; saying so
is better than quietly auditing a channel with no numbers in it.
"""
import csv
from datetime import datetime

from paths import data_path

STUDIO_DATE = '%b %d, %Y'

CSV_EXPORT_HELP = (
    'In YouTube Studio: Analytics -> Advanced mode -> date range Lifetime -> '
    'Content tab -> Export current view -> Comma-separated values (.csv), then '
    'unzip it and put "Table data.csv" there. It is the only source of publish '
    'dates, durations, thumbnail impressions and click-through rate.'
)

REQUIRED_COLUMNS = (
    'Content',
    'Video publish time',
    'Duration',
    'Views',
    'Watch time (hours)',
    'Thumbnail impressions',
    'Thumbnail click-through rate (%)',
)

SWITCH_TO_ENGLISH = ('Switch Studio to English (the gear at the bottom of the left menu -> '
                     'Language) and export again.')


def require_columns(table, header):
    """The export is only usable when Studio wrote the English column names this reads."""
    missing = [column for column in REQUIRED_COLUMNS if column not in (header or [])]
    if not missing:
        return
    raise SystemExit(
        f'The YouTube Studio export at {table} is missing columns this audit needs:\n'
        + '\n'.join(f'  {column}' for column in missing)
        + '\nIts columns are: ' + ', '.join(header or ['(none)'])
        + '\n\nTwo things cause this.\n\n'
          '1. The wrong report was exported. It has to be the Content tab, not Reach, not '
          'Audience, not one video\'s own analytics.\n'
        + f'   {CSV_EXPORT_HELP}\n\n'
        + '2. YouTube Studio is not set to English, so it wrote the column names '
        + f'translated. {SWITCH_TO_ENGLISH}')


def studio_rows(work_dir):
    """The Studio export keyed by video id, without its Total row."""
    table = data_path(work_dir, 'csv', 'Table data.csv')
    if not table.exists():
        raise SystemExit(f'No YouTube Studio export at {table}.\n{CSV_EXPORT_HELP}')
    rows = csv.DictReader(table.open())
    require_columns(table, rows.fieldnames)
    return {row['Content'].strip(): row for row in rows
            if row['Content'].strip() != 'Total'}


def published_date(row):
    """Studio's publish date. Blank only for an upload that was never published."""
    stamp = (row.get('Video publish time') or '').strip()
    if not stamp:
        return None
    try:
        return datetime.strptime(stamp, STUDIO_DATE).date().isoformat()
    except ValueError as unreadable:
        raise SystemExit(
            f'The Studio export gives video {row.get("Content")} the publish date "{stamp}", '
            f'which is not a date this audit can read.\nDates have to look like '
            f'"Aug 10, 2026". Another shape means YouTube Studio is not set to English. '
            f'{SWITCH_TO_ENGLISH}') from unreadable
