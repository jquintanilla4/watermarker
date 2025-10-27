# Video Watermarker

Interactive Python CLI to watermark a single video or all videos in a directory with a centered two-line text watermark. Coverage and opacity are configurable (defaults: 50% coverage, 15% opacity). Output files are saved alongside the source video(s) with unique names to avoid overwriting.

## Launchers

- macOS: double‑click `launcher.command`.
  - If it doesn’t run: right‑click `launcher.command` > Open. If needed, run once in Terminal: `chmod +x launcher.command`.
  - If macOS warns it’s from the Internet, you can clear quarantine: `xattr -d com.apple.quarantine launcher.command`.
- Windows: double‑click `launcher.bat` (requires Git for Windows, which provides Git Bash). Download from https://gitforwindows.org/.
- Linux and power users: run `./launcher.sh` in a terminal.

## Features

- Rich-powered interactive CLI with path validation and guided prompts
- Single file or directory batch processing
- Centered two-line text watermark with adjustable width coverage (1–100%) and opacity (0–100%)
- True per‑pixel alpha blending for smoother results
- Automatic text sizing that adapts to video resolution and requested coverage
- Non-destructive output naming (`*_watermarked.mp4`, `*_watermarked_copy.mp4`, ...)
- Supports common video formats (MP4, AVI, MOV, MKV, WebM, etc.)
- Saves results next to the original video(s) to keep workflow simple

## Requirements

- Python 3.8+
- OpenCV (`opencv-python`)
- Pillow (`Pillow`)
- NumPy (`numpy`)
- Rich (`rich`)
- Questionary (`questionary`)
- ffmpeg (for copying original audio into the watermarked output)

Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the script:
```bash
python3 video_watermarker.py
```

Follow the prompts:
- Choose what to watermark (use the arrow keys to pick single video or directory)
- Provide the file or directory path
- Enter watermark text (two lines; at least one line required)
- Select watermark coverage (percentage of frame width the widest text line should span; default 50%)
- Select watermark opacity (transparency of the text; default 15%)

The script prints video info and progress as it processes frames, then writes the output alongside each source video. If a file with the intended name already exists, a copy suffix is added to keep existing files intact.

## Example

```
=== Video Watermarker ===

? What would you like to watermark?  (Use arrow keys)
❯ Single video
  Directory of videos

? Enter the path to your video file: test_video/sample.mp4
? Watermark text - Line 1 (optional): Copyright 2024
? Watermark text - Line 2 (optional):

Coverage controls how much screen area the text occupies; opacity controls transparency.
Watermark coverage percentage (1-100%) [50]: 60
Watermark opacity percentage (0-100%) [15]: 20

Video info:
Resolution: 1920x1080
FPS: 30.0
Total frames: 900

Processing video...
Progress: 10.0%
...

Watermarked video saved as: test_video/sample_watermarked.mp4
```

## Notes

- The watermark is drawn as centered text; it does not place an opaque box over the video.
- Coverage percentage targets the widest text line to span that fraction of the frame width (50% roughly matches the previous behaviour).
- Opacity is configurable at runtime; adjust the default in `video_watermarker.py` if you want a different starting value.
- If ffmpeg is not installed or fails, the script falls back to a silent output video and prints a warning.
- Outputs are stored next to the original video files, so running from any working directory keeps results with their sources.
- The script attempts to use common system fonts (Arial/Helvetica on macOS, DejaVuSans on Linux, Arial on Windows) and falls back to a default font if unavailable.

### Troubleshooting launchers

- If double‑clicking `launcher.sh` just opens a text editor, use the platform wrappers above:
  - macOS: `launcher.command`
  - Windows: `launcher.bat`
- If a launcher doesn’t run due to permissions, mark it executable:
  - macOS/Linux: `chmod +x launcher.sh launcher.command`
- If Windows can’t find Bash, install Git for Windows (Git Bash) or run the app directly with Python: `py -3 video_watermarker.py`.
