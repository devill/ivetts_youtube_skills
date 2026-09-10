#!/usr/bin/env python3
"""Google OAuth for the end screen audit: one token cache, two YouTube scopes.

TWO WAYS TO USE THIS FILE:
    Run it    -- `python3 auth.py --work DIR` opens Google's browser consent
                 screen and writes DIR/token.json. Needs a human at a normal
                 terminal window; an agent session cannot drive it.
    Import it -- `load_credentials(work_dir)` gives the other scripts
                 ready-to-use credentials, refreshing a stale token silently.
                 It never opens a browser.
"""

import argparse
import json
import socket
from pathlib import Path

from google.auth.exceptions import RefreshError, TransportError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCRIPT_PATH = Path(__file__).resolve()
DEFAULT_WORK_DIR = 'endscreen-audit'

# captions.download needs the full force-ssl scope; the analytics reports need
# the read-only analytics scope. One cache carries both, so one consent serves
# every script here.
SCOPES = [
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/yt-analytics.readonly',
]

# Captured before prefer_ipv4() can replace it, so repeated calls always wrap
# the real resolver instead of stacking a filter on top of a filter.
UNFILTERED_GETADDRINFO = socket.getaddrinfo


def prefer_ipv4() -> None:
    """Put IPv4 first for every DNS lookup this process makes from now on.

    On a host whose IPv6 route to Google is dead, Python waits instead of
    falling back: creds.refresh() burns google-auth's 120 second timeout, and
    googleapiclient's httplib2 raises on the first address rather than trying
    the next family, so one AAAA record fails an API call outright. Deliberately
    process-wide, not scoped to the auth calls — the API calls need it too.
    A host with no IPv4 keeps the addresses it has, so nobody is stranded.
    """

    def ipv4_first(*args, **kwargs):
        addresses = UNFILTERED_GETADDRINFO(*args, **kwargs)
        ipv4 = [info for info in addresses if info[0] == socket.AF_INET]
        return ipv4 or addresses

    socket.getaddrinfo = ipv4_first


def work_dir_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--work', default=DEFAULT_WORK_DIR,
                        help='working directory holding client_secret.json, '
                             'token.json and data/ (default: %(default)s)')
    return parser


def resolve_work_dir(work: str) -> Path:
    work_dir = Path(work).expanduser().resolve()
    (work_dir / 'data').mkdir(parents=True, exist_ok=True)
    return work_dir


def data_path(work_dir: Path, *parts: str) -> Path:
    return work_dir.joinpath('data', *parts)


def load_json(path: Path):
    """Read a JSON file, naming it when a hand-typed one is malformed."""
    try:
        return json.loads(Path(path).read_text())
    except json.JSONDecodeError as malformed:
        raise SystemExit(f'{path} is not valid JSON: {malformed}') from malformed


def client_secret_file(work_dir: Path) -> Path:
    secret = work_dir / 'client_secret.json'
    if not secret.exists():
        raise SystemExit(
            f'No client_secret.json in {work_dir}.\n'
            'In the Google Cloud Console, enable the YouTube Data API v3 and the '
            'YouTube Analytics API, create an OAuth client of type "Desktop app", '
            f'download its JSON and save it as {secret}.'
        )
    return secret


class LoginNeeded(SystemExit):
    """The 'only a human can fix this' exit, worded the same way everywhere."""

    def __init__(self, work_dir: Path, reason: str):
        super().__init__(
            f'{reason}.\n'
            "Google's consent screen needs a browser, so a human has to do this in "
            'a normal terminal window — an agent session cannot drive it:\n'
            f'    python3 {SCRIPT_PATH} --work {work_dir}\n'
            'then re-run this command.'
        )


def read_token(token_file: Path) -> Credentials | None:
    """Parse the token cache. None if it is missing, malformed or incomplete."""
    if not token_file.exists():
        return None
    try:
        return Credentials.from_authorized_user_file(str(token_file))
    except ValueError:
        return None


def load_credentials(work_dir: Path) -> Credentials:
    """Credentials from the token cache, refreshed if stale. Never opens a browser."""
    prefer_ipv4()
    token_file = work_dir / 'token.json'

    creds = read_token(token_file)
    if creds is None:
        raise LoginNeeded(work_dir, f'no usable token cache at {token_file}')

    if creds.valid:
        return creds

    try:
        creds.refresh(Request())
    except RefreshError as rejected:
        raise LoginNeeded(
            work_dir, f'Google rejected the saved credentials ({rejected})'
        ) from rejected
    except TransportError as unreachable:
        raise SystemExit(
            f'Could not reach Google to refresh the token ({unreachable}).\n'
            'That is a network fault, not an expired login — no browser consent '
            'will help. Check the connection and re-run this command.'
        ) from unreachable

    token_file.write_text(creds.to_json())
    return creds


def authorise(work_dir: Path) -> None:
    secret = client_secret_file(work_dir)
    print(f'Opening a browser to authorise {len(SCOPES)} scope(s). Approve it there.')
    flow = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES)
    creds = flow.run_local_server(port=0)
    (work_dir / 'token.json').write_text(creds.to_json())


def main():
    prefer_ipv4()
    args = work_dir_parser(__doc__).parse_args()
    work_dir = resolve_work_dir(args.work)
    authorise(work_dir)
    print(f'{work_dir / "token.json"}: written')


if __name__ == '__main__':
    main()
