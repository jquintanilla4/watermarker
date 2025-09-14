# Video Watermarker

Interactive Python CLI to watermark a single video or all videos in a directory with a centered two-line text watermark at approximately 10% opacity. Output files are saved to `output_videos/` with unique names to avoid overwriting.

## Features

- Interactive command-line interface with path validation
- Single file or directory batch processing
- Centered two-line text watermark (~10% opacity)
- Automatic text sizing based on video resolution
- Non-destructive output naming (`*_watermarked.mp4`, `*_watermarked_copy.mp4`, ...)
- Supports common video formats (MP4, AVI, MOV, MKV, WebM, etc.)
- Saves results to `output_videos/`

## Requirements

- Python 3.8+
- OpenCV (`opencv-python`)
- Pillow (`Pillow`)
- NumPy (`numpy`)
- Inquirer (`inquirer`)

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
- Choose what to watermark: single file or all videos in a directory
- Provide the file or directory path
- Enter watermark text (two lines; at least one line required)

The script prints video info and progress as it processes frames, then writes the output to the `output_videos/` folder. If a file with the intended name already exists, a copy suffix is added to keep existing files intact.

## Example

```
=== Video Watermarker ===

? What would you like to watermark?  (Use arrow keys)
❯ Single video file
  All videos in a directory

Enter the path to your video file: test_video/sample.mp4
Enter watermark text - Line 1: Copyright 2024
Enter watermark text - Line 2: My Company Name

Video info:
Resolution: 1920x1080
FPS: 30.0
Total frames: 900

Processing video...
Progress: 10.0%
...

Watermarked video saved as: output_videos/sample_watermarked.mp4
```

## Notes

- The watermark is drawn as centered text; it does not place an opaque box over the video.
- Effective visibility is light (~10% of white). To make it stronger or lighter, adjust `alpha` in `add_watermark_to_video` and/or the RGBA text alpha in `create_watermark_overlay`.
- The script attempts to use system fonts (Arial or Helvetica on macOS) and falls back to a default font if unavailable.
