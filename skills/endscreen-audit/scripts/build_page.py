#!/usr/bin/env python3
"""Fold the audit data into one page with two views: the map and the repairs.

    python3 build_page.py --work DIR

Reads DIR/data/graph.json, and DIR/data/actions.json and DIR/data/channel.json when
they exist. Writes DIR/end-screen-audit.html (open this one from disk) and
DIR/data/artifact.html (the same body, for publishing with the Artifact tool).
"""

import json
from pathlib import Path

import repairs
from auth import data_path, load_json, resolve_work_dir, work_dir_parser

HERE = Path(__file__).resolve().parent
PAGE_NAME = 'end-screen-audit.html'

DOCUMENT_HEAD = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                 '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                 '</head>\n<body>\n')

TABS = '''<div class="views" role="tablist" aria-label="View">
    <button type="button" class="view-tab" role="tab" id="tab-map" data-view="map"
            aria-controls="view-map" aria-selected="true">Map</button>
    <button type="button" class="view-tab" role="tab" id="tab-repairs" data-view="repairs"
            aria-controls="view-repairs" aria-selected="false" tabindex="-1">Repairs</button>
  </div>'''


def read_json(path, fallback=None):
    if not path.exists():
        if fallback is None:
            raise SystemExit(f'No {path}. Run build_data.py --work {path.parent.parent} first.')
        return fallback
    return load_json(path)


def channel_line(channel):
    title = channel.get('title')
    return f'<p class="channel">{repairs.escape(title)}</p>' if title else ''


def embedded(graph):
    """graph.json as a JS literal that cannot end the script element early."""
    return json.dumps(graph).replace('</', '<\\/')


def build_body(graph, actions, channel):
    repairs_view = repairs.view(actions, {node['id']: node for node in graph['nodes']})
    head = (HERE / 'template_head.html').read_text()
    head = (head
            .replace('__CHANNEL__', channel_line(channel))
            .replace('__TABS__', TABS if repairs_view else '')
            .replace('__REPAIRS__', repairs_view))
    script = (HERE / 'template_script.html').read_text().replace('__GRAPH__', embedded(graph))
    return head + script


def main():
    args = work_dir_parser(__doc__).parse_args()
    work_dir = resolve_work_dir(args.work)

    body = build_body(read_json(data_path(work_dir, 'graph.json')),
                      read_json(data_path(work_dir, 'actions.json'), fallback={}),
                      read_json(data_path(work_dir, 'channel.json'), fallback={}))

    # The artifact host supplies <!doctype>, <head> and <meta charset>; a file opened
    # from disk gets none of them, so the local copy carries its own.
    data_path(work_dir, 'artifact.html').write_text(body, encoding='utf-8')
    page = work_dir / PAGE_NAME
    page.write_text(DOCUMENT_HEAD + body + '\n</body>\n</html>\n', encoding='utf-8')
    print(f'{page}: {page.stat().st_size // 1024} KB')


if __name__ == '__main__':
    main()
