"""Render the Repairs view: the worklist read out of actions.json.

Every section is skipped when its bucket is empty, so a partial actions.json
still produces a page that reads as finished.
"""

import html

EFFORT_CLASS = {'5 min': 'quick', '15 min': 'medium', 'session': 'long'}

BUCKET_KEYS = {
    'plan': ('id', 'effort', 'do', 'why'),
    'unmet': ('id', 'said', 'gap', 'fix'),
    'stale': ('id', 'said', 'delivered', 'fix'),
    'free': ('id', 'outro', 'target'),
    'trim': ('id', 'why', 'fix'),
    'thumbnails': ('id', 'note'),
}

SHAPE = ('{"unmet": [...], "stale": [...], "free": [...], "trim": [...], "thumbnails": [...], '
         '"destinations": [...], "plan": [...]}')

INTRO = ('What each published long-form video promises out loud at the end, what its end screen '
         'actually does, and the smallest change that closes the gap.')


def clock(seconds):
    """A duration as m:ss. Any figure can be missing; an em dash says so."""
    return '—' if seconds is None else f'{seconds // 60}:{seconds % 60:02d}'


def number(value):
    return '—' if value is None else f'{value:,}'


def percent(value, places=1):
    return '—' if value is None else f'{value:.{places}f}%'


def escape(text):
    return html.escape(str(text), quote=False)


def watch_url(video_id):
    return f'https://www.youtube.com/watch?v={video_id}'


def picture(video):
    """A thumbnail, or the same blank placeholder the map draws when there is none."""
    if not video['thumbnail']:
        return '<div class="blank">No thumbnail</div>'
    return f'<img src="{video["thumbnail"]}" alt="">'


class Repairs:
    """Every section reads videos out of the graph, so they share one lookup."""

    def __init__(self, actions, nodes_by_id):
        self.actions = actions
        self.nodes = nodes_by_id

    def video(self, video_id):
        if video_id not in self.nodes:
            raise SystemExit(f'actions.json names {video_id}, which is not in graph.json. '
                             'Rebuild graph.json, or fix the id.')
        return self.nodes[video_id]

    def own_video(self, video_id):
        """A video the creator can actually repair, and the only kind that carries stats."""
        video = self.video(video_id)
        if video.get('outside'):
            raise SystemExit(f'actions.json asks for a repair on {video_id} '
                             f'("{video["title"]}"), which is not one of this channel\'s '
                             'published long-form videos — it is only on the map as somewhere '
                             'an end screen points. Fix the id, or drop the entry.')
        return video

    # ---- one video, as a card ----

    def card(self, video_id, body):
        video = self.own_video(video_id)
        return f'''<li class="item">
  <a class="shot" href="{watch_url(video_id)}" target="_blank" rel="noopener">
    {picture(video)}</a>
  <div class="body">
    <h3><a href="{watch_url(video_id)}" target="_blank" rel="noopener">{escape(video['title'])}</a></h3>
    <p class="meta">{video['published']} &middot; {self.stats(video)}</p>
    {body}
  </div>
</li>'''

    @staticmethod
    def stats(video):
        return (f"{number(video['views'])} views &middot; "
                f"{percent(video['clickThroughRate'], 2)} CTR &middot; "
                f"{clock(video['averageViewDuration'])} avg &middot; "
                f"{percent(video['averageViewPercentage'])} watched")

    # ---- sections ----

    def plan_section(self):
        days = []
        for day, entry in enumerate(self.actions.get('plan', []), 1):
            video = self.own_video(entry['id'])
            effort = entry['effort']
            days.append(f'''<li class="day">
  <div class="daymark"><span class="daynum">{day}</span>
    <span class="effort {EFFORT_CLASS.get(effort, 'medium')}">{escape(effort)}</span></div>
  <a class="shot" href="{watch_url(entry['id'])}" target="_blank" rel="noopener">
    {picture(video)}</a>
  <div class="body">
    <h3>{escape(entry['do'])}</h3>
    <p class="meta">{escape(video['title'])}</p>
    <p>{escape(entry['why'])}</p>
  </div>
</li>''')
        if not days:
            return ''
        return wrap('One a day, highest leverage first', len(days),
                    'Ordered by what each change is worth, not by how long it takes. Most are a '
                    'few minutes in Studio; the ones marked as a session need a real design sitting '
                    '&mdash; do those on the days you have the energy.',
                    f'<ol class="days">{"".join(days)}</ol>')

    def unmet_section(self):
        items = [self.card(entry['id'], said_and_fix(
            entry, extra=labelled('The gap', entry['gap'])))
            for entry in self.actions.get('unmet', [])]
        return listing('Promises with nothing behind them', items,
                       'The outro names a video that was never released, or points at one that '
                       'viewers cannot watch.')

    def stale_section(self):
        items = []
        for entry in self.actions.get('stale', []):
            delivered = self.video(entry['delivered'])
            extra = labelled('Already released',
                             f'{escape(delivered["title"])} &mdash; {delivered["published"]}',
                             raw=True)
            items.append(self.card(entry['id'], said_and_fix(entry, extra=extra)))
        return listing('Promises kept, end screen never updated', items,
                       'The follow-up exists. The end screen still does not point at it.')

    def free_section(self):
        items = []
        for entry in self.actions.get('free', []):
            target = entry['target']
            fix = ('Already correct &mdash; leave it.' if target is None
                   else f'Pin &ldquo;{escape(self.video(target)["title"])}&rdquo;.')
            items.append(self.card(entry['id'],
                                   labelled('The outro says', entry['outro'])
                                   + labelled('Do this', fix, raw=True)))
        return listing('Outros that fit any link', items,
                       'Nothing specific is promised out loud, so the end screen can point wherever '
                       'you like without re-recording a second of audio. This is where the easy '
                       'wins are.')

    def trim_section(self):
        items = [self.card(entry['id'],
                           labelled('Why', entry['why']) + labelled('Do this', entry['fix']))
                 for entry in self.actions.get('trim', [])]
        return listing('Outros worth trimming', items,
                       'Dated plugs and promises that pin the ending to a moment that has passed. '
                       'Cutting them frees the end screen to match anything.')

    def thumbnail_section(self):
        items = [self.card(entry['id'], labelled('Why', entry['note']))
                 for entry in self.actions.get('thumbnails', [])]
        return listing('Thumbnails worth redoing', items,
                       'Low click-through rate, healthy watch time. People who click stay, so the '
                       'thumbnail is what is costing views &mdash; not the video.')

    def destinations_section(self):
        rows = []
        for video_id in self.actions.get('destinations', []):
            video = self.own_video(video_id)
            rows.append(f'''<tr>
  <td>{escape(video['title'])}</td>
  <td class="num">{video['published']}</td>
  <td class="num">{clock(video['averageViewDuration'])}</td>
  <td class="num">{percent(video['averageViewPercentage'])}</td>
  <td class="num">{percent(video['clickThroughRate'], 2)}</td>
</tr>''')
        if not rows:
            return ''
        table = f'''<div class="scroller"><table>
    <thead><tr><th>Video</th><th class="num">Published</th><th class="num">Avg view time</th>
      <th class="num">Avg view %</th><th class="num">CTR</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table></div>'''
        return wrap('Where to send people', len(rows),
                    'Recent videos that hold attention once someone arrives. Every recommendation '
                    'above points at one of these.', table)

    def sections(self):
        return '\n'.join(filter(None, [
            self.plan_section(), self.unmet_section(), self.stale_section(), self.free_section(),
            self.trim_section(), self.thumbnail_section(), self.destinations_section(),
        ]))


def labelled(label, text, raw=False):
    return f'<p><span class="label">{label}</span> {text if raw else escape(text)}</p>'


def said_and_fix(entry, extra=''):
    return labelled('The outro says', entry['said']) + extra + labelled('Do this', entry['fix'])


def listing(heading, items, note):
    if not items:
        return ''
    return wrap(heading, len(items), note, '<ol class="items">\n' + '\n'.join(items) + '\n</ol>')


def wrap(heading, how_many, note, body):
    return (f'<section>\n<h2><span class="how-many">{how_many}</span> {heading}</h2>\n'
            f'<p class="note">{note}</p>\n{body}\n</section>')


def entry_name(bucket, position, entry):
    video_id = entry.get('id') if isinstance(entry, dict) else None
    return f'the "{bucket}" entry for {video_id}' if video_id else f'"{bucket}" entry {position}'


def require_object(actions):
    if isinstance(actions, dict):
        return
    raise SystemExit(f'actions.json is a JSON {type(actions).__name__}, and it has to be an '
                     f'object keyed by bucket:\n  {SHAPE}\nSee reference/actions.md.')


def require_keys(actions):
    """A bucket entry short of a key would otherwise die deep inside rendering the page."""
    for bucket, keys in BUCKET_KEYS.items():
        for position, entry in enumerate(actions.get(bucket, []), 1):
            missing = [key for key in keys if key not in entry]
            if missing:
                raise SystemExit(
                    f'In actions.json, {entry_name(bucket, position, entry)} has no '
                    + ', '.join(f'"{key}"' for key in missing)
                    + f'. Every "{bucket}" entry needs '
                    + ', '.join(f'"{key}"' for key in keys)
                    + '. See reference/actions.md.')


def view(actions, nodes_by_id):
    """The whole Repairs panel, or '' when there is nothing to repair."""
    require_object(actions)
    require_keys(actions)
    sections = Repairs(actions, nodes_by_id).sections()
    if not sections:
        return ''
    return f'''<div class="view" id="view-repairs" data-view="repairs" role="tabpanel"
     aria-labelledby="tab-repairs" hidden>
  <div class="page">
    <p class="view-note">{INTRO}</p>
    {sections}
  </div>
</div>'''
