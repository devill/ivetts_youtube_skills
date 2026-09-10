#!/usr/bin/env python3
"""Where the audit keeps its files, and how every script agrees on them.

The work directory holds data/ (everything the scripts read and write) and an
optional config.json. Nothing here reaches the network: the browser reads
YouTube Studio, and these scripts only ever see the files it left behind.
"""

import argparse
import json
from pathlib import Path

DEFAULT_WORK_DIR = 'endscreen-audit'


def work_dir_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--work', default=DEFAULT_WORK_DIR,
                        help='working directory holding data/ and config.json '
                             '(default: %(default)s)')
    return parser


def resolve_work_dir(work: str) -> Path:
    work_dir = Path(work).expanduser().resolve()
    if not work_dir.is_dir():
        raise SystemExit(f'No working directory at {work_dir}.\nCheck the --work path. The '
                         'directory has to exist already: it is where the Studio reads were '
                         'collected.')
    (work_dir / 'data').mkdir(exist_ok=True)
    return work_dir


def data_path(work_dir: Path, *parts: str) -> Path:
    return work_dir.joinpath('data', *parts)


def load_json(path: Path, produced_by: str = ''):
    """Read a JSON file, naming it when it is missing or a hand-typed one is malformed."""
    path = Path(path)
    if not path.exists():
        raise SystemExit(f'No {path}.' + (f'\n{produced_by}' if produced_by else ''))
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as malformed:
        raise SystemExit(f'{path} is not valid JSON: {malformed}') from malformed
