#!/usr/bin/env python3
"""Export marked candidates as Premiere XML, FCPXML, and CMX3600 EDL."""

import argparse
import html
import json
import subprocess
from pathlib import Path
from urllib.parse import quote


class ProbeCache:
    """ffprobe results per clip, parsed from structured JSON so stream order never matters."""

    def __init__(self):
        self.values = {}

    def inspect(self, path):
        key = str(path)
        if key not in self.values:
            command = [
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration:stream=codec_type,r_frame_rate,width,height",
                "-of", "json", str(path),
            ]
            try:
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                data = json.loads(result.stdout)
            except (OSError, subprocess.CalledProcessError, json.JSONDecodeError, KeyError, ValueError) as error:
                raise SystemExit(f"Media file missing or unreadable: {path.name}") from error
            video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
            duration = float(data["format"]["duration"])
            rate = video.get("r_frame_rate", "30/1")
            width = int(video.get("width", 1920))
            height = int(video.get("height", 1080))
            self.values[key] = (duration, rate, width, height)
        return self.values[key]


def normalise_id(identifier):
    clip, _, start = identifier.rpartition("|")
    return f"{clip}|{float(start):.4f}"


def candidate_id(candidate):
    return f"{candidate['clip']}|{float(candidate['start']):.4f}"


def parse_rate(rate_text):
    try:
        if "/" in rate_text:
            numerator, denominator = rate_text.split("/", 1)
            numerator, denominator = int(numerator), int(denominator)
        else:
            numerator, denominator = int(float(rate_text)), 1
        if numerator <= 0 or denominator <= 0:
            raise ValueError
        return numerator, denominator
    except (TypeError, ValueError):
        raise SystemExit("--fps must look like 25 or 30000/1001")


def frame_count(seconds, numerator, denominator):
    return round(seconds * numerator / denominator)


def timecode(frame, timebase):
    frame = int(frame)
    hours, remainder = divmod(frame // timebase, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frame % timebase:02d}"


def load_events(work, media, tail, preroll, fps_override, probe):
    candidates_path = work / "candidates.json"
    selections_path = work / "selections.json"
    if not candidates_path.exists():
        raise SystemExit(f"Missing {candidates_path}; create candidates.json first.")
    if not selections_path.exists():
        raise SystemExit(f"Missing {selections_path}; create selections.json first.")

    sections = json.loads(candidates_path.read_text())
    selections = json.loads(selections_path.read_text())
    marks = {normalise_id(key): value for key, value in selections.get("marks", {}).items()}
    candidate_sections = {}
    for section in sections:
        for candidate in section["candidates"]:
            identity = candidate_id(candidate)
            if identity in candidate_sections:
                raise SystemExit(f"Duplicate candidate id {identity} in sections {candidate_sections[identity]!r} and {section['label']!r}.")
            candidate_sections[identity] = section["label"]
    first_marked = next(
        (candidate for section in sections for candidate in section["candidates"]
         if marks.get(candidate_id(candidate), {}).get("state") in ("use", "maybe")),
        None,
    )
    if first_marked is None:
        raise SystemExit("Nothing is marked use or maybe in selections.json.")

    first_path = media / f"{first_marked['clip']}.mp4"
    _, probed_rate, width, height = probe.inspect(first_path)
    numerator, denominator = parse_rate(fps_override) if fps_override != "auto" else parse_rate(probed_rate)
    fps = numerator / denominator
    timebase = round(fps)
    events = []
    timeline_frame = 0
    for section in sections:
        for candidate in section["candidates"]:
            mark = marks.get(candidate_id(candidate), {})
            state = mark.get("state")
            if state not in ("use", "maybe"):
                continue
            clip_path = media / f"{candidate['clip']}.mp4"
            duration, _, _, _ = probe.inspect(clip_path)
            real_end = frame_count(duration, numerator, denominator)
            source_start = max(0, frame_count(float(candidate["start"]) - preroll, numerator, denominator))
            source_end = min(
                real_end - 1,
                frame_count(float(candidate["end"]) + tail, numerator, denominator),
            )
            event_duration = max(1, source_end - source_start)
            events.append({
                "section": section,
                "candidate": candidate,
                "state": state,
                "source_start": source_start,
                "source_end": source_end,
                "duration": event_duration,
                "timeline_start": timeline_frame,
                "asset_duration": real_end,
            })
            timeline_frame += event_duration
    return events, numerator, denominator, timebase, width, height


def media_url(media, clip):
    return "file://localhost/" + quote(str((media / f"{clip}.mp4").resolve()), safe="/")


def xml_rate(timebase, ntsc):
    return f"<rate><timebase>{timebase}</timebase><ntsc>{str(ntsc).upper()}</ntsc></rate>"


def xmeml_document(events, name, media, timebase, ntsc, width, height):
    rate_xml = xml_rate(timebase, ntsc)
    file_ids = {clip: index for index, clip in enumerate(dict.fromkeys(
        event["candidate"]["clip"] for event in events), 1)}
    first_reference = set()
    video_items, audio_items = [], []
    for index, event in enumerate(events, 1):
        candidate = event["candidate"]
        clip = candidate["clip"]
        file_id = file_ids[clip]
        file_block = f'<file id="f{file_id}"/>'
        if clip not in first_reference:
            first_reference.add(clip)
            file_block = (
                f'<file id="f{file_id}"><name>{html.escape(clip)}.mp4</name>'
                f'<pathurl>{media_url(media, clip)}</pathurl>{rate_xml}'
                f'<duration>{event["asset_duration"]}</duration>'
                f'<timecode>{rate_xml}<string>00:00:00:00</string><frame>0</frame>'
                f'<displayformat>NDF</displayformat></timecode><media><video>'
                f'<samplecharacteristics>{rate_xml}<width>{width}</width>'
                f'<height>{height}</height></samplecharacteristics></video><audio>'
                f'<channelcount>2</channelcount><samplecharacteristics><depth>16</depth>'
                f'<samplerate>48000</samplerate></samplecharacteristics></audio></media></file>'
            )
        label = (("MAYBE " if event["state"] == "maybe" else "") + event["section"]["label"])[:28]
        links = (
            f"<link><linkclipref>v{index}</linkclipref><mediatype>video</mediatype>"
            f"<trackindex>1</trackindex><clipindex>{index}</clipindex></link>"
            f"<link><linkclipref>a{index}</linkclipref><mediatype>audio</mediatype>"
            f"<trackindex>1</trackindex><clipindex>{index}</clipindex></link>"
        )
        span = (
            f"<duration>{event['asset_duration']}</duration>{rate_xml}"
            f"<start>{event['timeline_start']}</start>"
            f"<end>{event['timeline_start'] + event['duration']}</end>"
            f"<in>{event['source_start']}</in><out>{event['source_end']}</out>{file_block}{links}"
        )
        video_enabled = "FALSE" if event["state"] == "maybe" else "TRUE"
        video_items.append(
            f'<clipitem id="v{index}"><name>{html.escape(label)}</name>'
            f'<enabled>{video_enabled}</enabled>{span}'
            f'<sourcetrack><mediatype>video</mediatype></sourcetrack></clipitem>')
        audio_items.append(
            f'<clipitem id="a{index}"><name>{html.escape(label)}</name>'
            f'<enabled>TRUE</enabled>{span}'
            f'<sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack></clipitem>')

    markers = []
    seen = set()
    for event in events:
        key = event["section"]["key"]
        if key in seen:
            continue
        seen.add(key)
        label = f"SCENE {len(markers) + 1}: {event['section']['label']}"
        markers.append(f'<marker><comment>{html.escape(label)}</comment><name>{html.escape(label)}</name><in>{event["timeline_start"]}</in><out>-1</out></marker>')
    rate = xml_rate(timebase, ntsc)
    total = events[-1]["timeline_start"] + events[-1]["duration"]
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4"><sequence><name>{html.escape(name)}</name><duration>{total}</duration>{rate}<timecode>{rate}<string>00:00:00:00</string><frame>0</frame><displayformat>NDF</displayformat></timecode>
<media><video><format><samplecharacteristics>{rate}<width>{width}</width><height>{height}</height><pixelaspectratio>square</pixelaspectratio></samplecharacteristics></format><track>{"".join(video_items)}</track></video>
<audio><format><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics></format><track>{"".join(audio_items)}</track></audio></media>{"".join(markers)}</sequence></xmeml>
'''


def fcpxml_document(events, name, media, numerator, denominator, width, height):
    clips = list(dict.fromkeys(event["candidate"]["clip"] for event in events))
    fps = numerator / denominator
    suffixes = {23.976: "2398", 24: "24", 25: "25", 29.97: "2997", 30: "30", 50: "50", 59.94: "5994", 60: "60"}
    fps_name = next((suffix for known_fps, suffix in suffixes.items() if abs(fps - known_fps) <= 0.01), str(round(fps)))
    format_name = f"FFVideoFormat{height}p{fps_name}"
    assets = []
    for index, clip in enumerate(clips, 1):
        duration = next(event["asset_duration"] for event in events if event["candidate"]["clip"] == clip)
        assets.append(f'<asset id="a{index}" name="{html.escape(clip)}" src="{media_url(media, clip)}" start="0s" duration="{duration / (numerator / denominator):.4f}s" hasVideo="1" hasAudio="1" format="r1"/>')
    spine = []
    for event in events:
        clip = event["candidate"]["clip"]
        label = ("MAYBE " if event["state"] == "maybe" else "") + event["section"]["label"]
        spine.append(f'<asset-clip ref="a{clips.index(clip) + 1}" offset="{event["timeline_start"] / (numerator / denominator):.4f}s" start="{event["source_start"] / (numerator / denominator):.4f}s" duration="{event["duration"] / (numerator / denominator):.4f}s" name="{html.escape(label)}"/>')
    total = events[-1]["timeline_start"] + events[-1]["duration"]
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml><fcpxml version="1.9"><resources>
<format id="r1" name="{format_name}" frameDuration="{denominator}/{numerator}s" width="{width}" height="{height}"/>{"".join(assets)}
</resources><library><event name="{html.escape(name)}"><project name="{html.escape(name)}"><sequence format="r1" duration="{total / (numerator / denominator):.4f}s"><spine>{"".join(spine)}</spine></sequence></project></event></library></fcpxml>
'''


def edl_document(events, name, timebase):
    lines = [f"TITLE: {name}", "FCM: NON-DROP FRAME", ""]
    for index, event in enumerate(events, 1):
        candidate = event["candidate"]
        flag = "  ; MAYBE" if event["state"] == "maybe" else ""
        lines.append(f"{index:03d}  Z{index:03d} V C        {timecode(event['source_start'], timebase)} {timecode(event['source_end'], timebase)} {timecode(event['timeline_start'], timebase)} {timecode(event['timeline_start'] + event['duration'], timebase)}")
        lines.append(f"* FROM CLIP NAME: {candidate['clip']}.mp4   ; scene: {event['section']['label']}{flag}")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Export marked rough-cut events in edit-friendly formats.")
    parser.add_argument("--work", required=True, help="Directory containing candidates.json and selections.json.")
    parser.add_argument("--media", required=True, help="Directory containing candidate MP4 files.")
    parser.add_argument("--name", default="Rough cut", help="Name for the exported sequence.")
    parser.add_argument("--tail", type=float, default=0.6, help="Seconds appended to each candidate.")
    parser.add_argument("--preroll", type=float, default=0.4, help="Seconds prepended to each candidate.")
    parser.add_argument("--fps", default="auto", help="Frame rate, such as auto, 25, or 30000/1001.")
    parser.add_argument("--formats", choices=("all", "premiere", "fcpxml", "edl"), default="all", help="Formats to write.")
    args = parser.parse_args()
    work, media = Path(args.work), Path(args.media)
    events, numerator, denominator, timebase, width, height = load_events(work, media, args.tail, args.preroll, args.fps, ProbeCache())
    ntsc = numerator / denominator != timebase
    outputs = []
    if args.formats in ("all", "premiere"):
        path = work / "rough-cut.xml"
        path.write_text(xmeml_document(events, args.name, media, timebase, ntsc, width, height))
        outputs.append(path)
    if args.formats in ("all", "fcpxml"):
        path = work / "rough-cut.fcpxml"
        path.write_text(fcpxml_document(events, args.name, media, numerator, denominator, width, height))
        outputs.append(path)
    if args.formats in ("all", "edl"):
        path = work / "rough-cut.edl"
        path.write_text(edl_document(events, args.name, timebase))
        outputs.append(path)
    total_frames = events[-1]["timeline_start"] + events[-1]["duration"]
    total_minutes = total_frames / (numerator / denominator) / 60
    maybe_count = sum(event["state"] == "maybe" for event in events)
    print(f"events: {len(events)}; duration: {total_minutes:.1f} minutes; maybes: {maybe_count}")
    for path in outputs:
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
