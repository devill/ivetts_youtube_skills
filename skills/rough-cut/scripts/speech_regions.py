#!/usr/bin/env python3
"""Detect speech regions in media clips using ffmpeg silencedetect."""

import argparse
import json
import re
import subprocess
from pathlib import Path


def probe_duration(path):
    command = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def has_audio_stream(path):
    command = ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "json", str(path)]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return any(stream.get("codec_type") == "audio" for stream in json.loads(result.stdout).get("streams", []))


def detect_silences(path, noise, minimum_silence):
    command = [
        "ffmpeg", "-hide_banner", "-i", str(path), "-af",
        f"silencedetect=noise={noise}:d={minimum_silence}", "-f", "null", "-",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    starts = [float(match.group(1)) for match in re.finditer(r"silence_start:\s*([\d.]+)", result.stderr)]
    ends = [float(match.group(1)) for match in re.finditer(r"silence_end:\s*([\d.]+)", result.stderr)]
    return starts, ends


def speech_regions(path, noise, minimum_silence, minimum_region):
    duration = probe_duration(path)
    if not has_audio_stream(path):
        return duration, []
    starts, ends = detect_silences(path, noise, minimum_silence)
    spans = []
    cursor = 0.0
    for index, start in enumerate(starts):
        if index < len(ends):
            end = ends[index]
            if start - cursor >= minimum_region:
                spans.append([round(cursor, 4), round(start, 4)])
            cursor = end
        else:
            if start - cursor >= minimum_region:
                spans.append([round(cursor, 4), round(start, 4)])
            cursor = duration
    if duration - cursor >= minimum_region:
        spans.append([round(cursor, 4), round(duration, 4)])
    return duration, spans


def main():
    parser = argparse.ArgumentParser(description="Find speech regions by inverting ffmpeg silencedetect output.")
    parser.add_argument("--media", required=True, help="Directory containing media clips.")
    parser.add_argument("--out", required=True, help="JSON file to write.")
    parser.add_argument("--noise", default="-30dB", help="Silencedetect noise threshold, for example -30dB.")
    parser.add_argument("--min-silence", type=float, default=2.0, help="Minimum silence duration in seconds.")
    parser.add_argument("--min-region", type=float, default=1.0, help="Minimum speech region duration in seconds.")
    parser.add_argument("--ext", default="mp4", help="Clip extension without a leading dot.")
    args = parser.parse_args()
    clips = sorted(Path(args.media).glob(f"*.{args.ext}"))
    result = {}
    total_regions = 0
    for clip in clips:
        duration, regions = speech_regions(clip, args.noise, args.min_silence, args.min_region)
        result[clip.stem] = {"duration": duration, "regions": regions}
        total_regions += len(regions)
        if not regions and not has_audio_stream(clip):
            print(f"{clip.name}: NO AUDIO STREAM")
        else:
            print(f"{clip.name}: {len(regions)} regions, {duration:.1f}s")
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n")
    print(f"total: {len(clips)} clips, {total_regions} regions")


if __name__ == "__main__":
    main()
