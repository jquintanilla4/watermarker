#!/usr/bin/env python3
"""
Simple Video Watermarker
Adds a centered two-line text watermark with configurable coverage and opacity.
"""

import cv2
import numpy as np
import os
import math
import questionary
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont
from rich.console import Console
from rich.prompt import Prompt

# Single console instance for Rich-powered interaction
console = Console()


def process_directory(directory_path, text_line1, text_line2, coverage_pct, opacity_pct):
    """Process all video files in a directory."""
    video_extensions = [
        ".mp4",
        ".avi",
        ".mov",
        ".mkv",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
    ]
    video_files = []

    # Find all video files in the directory
    for file in os.listdir(directory_path):
        if any(file.lower().endswith(ext) for ext in video_extensions):
            video_files.append(os.path.join(directory_path, file))

    if not video_files:
        console.print(
            f"\n[bold yellow]No video files found[/] in directory: [italic]{directory_path}[/]")
        return False

    console.print(
        f"\nFound [bold]{len(video_files)}[/] video file(s) to process:")
    for i, video_file in enumerate(video_files, 1):
        console.print(f"  {i}. {os.path.basename(video_file)}")

    console.print("\nProcessing videos...")
    successful = 0
    failed = 0

    for i, video_file in enumerate(video_files, 1):
        console.print(
            f"\n[bold cyan]--- Processing video {i}/{len(video_files)}:[/] {os.path.basename(video_file)} ---"
        )
        success = add_watermark_to_video(
            video_file, text_line1, text_line2, coverage_pct, opacity_pct
        )
        if success:
            successful += 1
        else:
            failed += 1

    console.print("\n[bold green]=== Batch Processing Complete ===[/]")
    console.print(f"Successfully processed: [bold]{successful}[/] videos")
    console.print(f"Failed: [bold red]{failed}[/] videos")

    return successful > 0


def get_unique_output_path(source_path):
    """Generate a unique output path beside the source video."""
    output_dir = os.path.dirname(source_path)
    base_name = os.path.splitext(os.path.basename(source_path))[0]
    base_output_path = os.path.join(output_dir, f"{base_name}_watermarked.mp4")

    if not os.path.exists(base_output_path):
        return base_output_path

    counter = 1
    while True:
        if counter == 1:
            copy_path = os.path.join(
                output_dir, f"{base_name}_watermarked_copy.mp4")
        else:
            copy_path = os.path.join(
                output_dir, f"{base_name}_watermarked_copy{counter}.mp4")

        if not os.path.exists(copy_path):
            return copy_path

        counter += 1


def create_watermark_overlay(
    frame_width,
    frame_height,
    text_line1,
    text_line2,
    coverage_pct,
    opacity_pct,
):
    """Create a watermark overlay image with text."""
    # Create transparent image for watermark
    overlay = Image.new("RGBA", (frame_width, frame_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Use full screen for centering text
    watermark_width = frame_width
    watermark_height = frame_height

    # Determine base font size prior to scaling tweaks
    base_font_size = max(
        60, min((watermark_width // 5), (watermark_height // 6)))

    # Try common cross-platform font locations; prefer bold variants when available
    font_candidates = [
        # macOS (bold variants first)
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/HelveticaNeue.ttf",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        # Windows
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf",
        # Regular fallbacks
        "/System/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
    ]
    font_path = None
    for path in font_candidates:
        if os.path.exists(path):
            try:
                ImageFont.truetype(path, base_font_size)
                font_path = path
                break
            except Exception:
                pass
    if font_path is None:
        font = ImageFont.load_default()
    else:
        font = ImageFont.truetype(font_path, base_font_size)

    def load_font(size: float) -> ImageFont.ImageFont:
        if font_path:
            adjusted = max(10, int(round(size)))
            try:
                return ImageFont.truetype(font_path, adjusted)
            except Exception:
                pass
        return ImageFont.load_default()

    def measure_text(font_obj: ImageFont.ImageFont):
        lines = []
        for text_value in (text_line1, text_line2):
            if not text_value.strip():
                continue
            bbox = draw.textbbox((0, 0), text_value, font=font_obj)
            if not bbox:
                continue
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            lines.append(
                {
                    "text": text_value,
                    "bbox": bbox,
                    "width": width,
                    "height": height,
                }
            )

        if not lines:
            # Fallback: include first line even if draw.textbbox failed (should be rare)
            fallback_text = text_line1 if text_line1.strip() else text_line2
            width = 0
            height = 0
            lines.append(
                {
                    "text": fallback_text,
                    "bbox": (0, 0, width, height),
                    "width": width,
                    "height": height,
                }
            )

        max_line_height = max(line["height"] for line in lines) if lines else 0
        spacing = int(max_line_height * 0.2) if len(lines) > 1 else 0
        total_text_height = sum(
            line["height"] for line in lines) + spacing * max(0, len(lines) - 1)
        max_text_width = max(line["width"] for line in lines) if lines else 0

        return {
            "lines": lines,
            "spacing": spacing,
            "total_height": total_text_height,
            "max_width": max_text_width,
        }

    metrics = measure_text(font)

    # Scale font size so the widest text line approximates the requested frame coverage
    target_width_ratio = max(coverage_pct, 1.0) / 100.0
    target_width_ratio = min(target_width_ratio, 1.0)

    if font_path and watermark_width > 0:
        current_size = float(base_font_size)
        for _ in range(6):
            width_ratio = (metrics["max_width"] /
                           watermark_width) if watermark_width else 0.0
            if width_ratio <= 0:
                break

            height_ratio = (metrics["total_height"] /
                            watermark_height) if watermark_height else 0.0
            # Prevent oversized height before attempting further scaling
            if height_ratio > 0.9:
                current_size = current_size * (0.9 / max(height_ratio, 1e-6))
                font = load_font(current_size)
                metrics = measure_text(font)
                continue

            if abs(width_ratio - target_width_ratio) <= 0.02:
                break

            scale_factor = target_width_ratio / max(width_ratio, 1e-6)
            current_size = current_size * scale_factor
            # Keep font size within sane bounds relative to frame height
            max_size = watermark_height * 0.9
            if current_size > max_size:
                current_size = max_size
            font = load_font(current_size)
            metrics = measure_text(font)

    # Recompute metrics one final time in case we exited early without an update
    metrics = measure_text(font)
    lines = metrics["lines"]
    spacing = metrics["spacing"]
    total_text_height = metrics["total_height"]

    # Center the text block in the watermark area
    start_y = (watermark_height - total_text_height) // 2

    # Draw text with user-configured opacity
    clamped_opacity = max(0.0, min(opacity_pct, 100.0))
    alpha_value = int(round(255 * (clamped_opacity / 100.0)))
    text_color = (255, 255, 255, alpha_value)

    current_y = start_y
    for idx, line in enumerate(lines):
        bbox = line["bbox"]
        line_width = line["width"]
        line_height = line["height"]
        x = (watermark_width - line_width) / 2.0 - bbox[0]
        y = current_y - bbox[1]
        draw.text((x, y), line["text"], font=font, fill=text_color)
        current_y += line_height
        if idx < len(lines) - 1:
            current_y += spacing

    return overlay


def mux_audio_into_video(original_video_path, watermarked_video_path, final_output_path):
    """Attempt to copy the original audio track into the processed video using ffmpeg."""

    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        console.print(
            "[bold yellow]Warning:[/] ffmpeg not found; output video will not include audio."
        )
        return False

    cmd = [
        ffmpeg_path,
        "-y",
        "-loglevel",
        "error",
        "-i",
        watermarked_video_path,
        "-i",
        original_video_path,
        "-map",
        "0:v:0",
        "-map",
        "1:a?",
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-movflags",
        "+faststart",
        final_output_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except Exception as exc:
        console.print(
            f"[bold yellow]Warning:[/] Failed to run ffmpeg to copy audio ({exc}). Video will be silent."
        )
        return False

    if result.returncode != 0:
        stderr_output = result.stderr.decode("utf-8", errors="ignore").strip()
        if stderr_output:
            console.print(
                "[bold yellow]Warning:[/] ffmpeg could not copy audio; video will be silent."
            )
            console.print(f"  ffmpeg output: {stderr_output}")
        else:
            console.print(
                "[bold yellow]Warning:[/] ffmpeg could not copy audio; video will be silent."
            )
        return False

    return True


def add_watermark_to_video(video_path, text_line1, text_line2, coverage_pct, opacity_pct):
    """Add watermark to video and save the result."""
    # Open video
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        console.print("[bold red]Error:[/] Could not open video file.")
        return False

    # Get video properties (guard against 0/NaN values)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    if (isinstance(fps, float) and math.isnan(fps)) or fps <= 0:
        fps = 30.0
    total_frames = int((cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) or 0)

    console.print("\n[bold]Video info:[/]")
    console.print(f"Resolution: {frame_width}x{frame_height}")
    console.print(f"FPS: {fps}")
    console.print(f"Total frames: {total_frames}")

    # Create output filename with unique path handling
    output_path = get_unique_output_path(video_path)

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Define codec and create VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    temp_video_path = f"{output_path}.video-only.mp4"
    if os.path.exists(temp_video_path):
        os.remove(temp_video_path)

    out = cv2.VideoWriter(temp_video_path, fourcc, fps,
                          (frame_width, frame_height))
    if not out.isOpened():
        console.print(
            "[bold red]Error:[/] Could not open VideoWriter with codec 'mp4v'.")
        cap.release()
        return False

    # Create watermark overlay once and prepare per-pixel alpha compositing
    watermark_overlay = create_watermark_overlay(
        frame_width,
        frame_height,
        text_line1,
        text_line2,
        coverage_pct,
        opacity_pct,
    )
    overlay_rgba = np.array(watermark_overlay)
    overlay_bgr = cv2.cvtColor(overlay_rgba[:, :, :3], cv2.COLOR_RGB2BGR)
    overlay_alpha = overlay_rgba[:, :, 3].astype(np.float32) / 255.0
    # Optional global strength multiplier (1.0 uses overlay alpha as-is)
    strength = 1.0
    mask = np.clip(overlay_alpha * strength, 0.0, 1.0)
    overlay_float = overlay_bgr.astype(np.float32)

    console.print("\nProcessing video...")
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Per-pixel alpha blend the overlay onto the frame in BGR space
        frame_float = frame.astype(np.float32)
        # Blend each color channel using the same alpha mask
        for c in range(3):
            frame_float[:, :, c] = (
                frame_float[:, :, c] * (1.0 - mask) +
                overlay_float[:, :, c] * mask
            )
        final_frame = np.clip(frame_float, 0, 255).astype(np.uint8)

        # Write frame
        out.write(final_frame)

        frame_count += 1
        if (
            total_frames > 0 and frame_count % 30 == 0
        ):  # Progress update every 30 frames
            progress = (frame_count / total_frames) * 100
            console.print(f"Progress: {progress:.1f}%")

    # Release everything
    cap.release()
    out.release()

    audio_copied = mux_audio_into_video(
        video_path, temp_video_path, output_path)
    if audio_copied:
        try:
            os.remove(temp_video_path)
        except OSError:
            pass
    else:
        if not os.path.exists(output_path):
            os.replace(temp_video_path, output_path)
        else:
            try:
                os.remove(temp_video_path)
            except OSError:
                pass

    console.print(
        f"\n[bold green]Watermarked video saved as:[/] {output_path}")
    return True


def _normalize_pasted_path(raw_path):
    if not isinstance(raw_path, str):
        return ""
    # Trim leading/trailing whitespace
    s = raw_path.strip()
    # Remove matching wrapping quotes while keeping interior characters intact
    if (len(s) >= 2) and s[0] in ('"', "'") and s[-1] == s[0]:
        s = s[1:-1]
    # Convert Finder-style escaped spaces to real spaces
    s = s.replace("\\ ", " ")
    # Keep spaces in path; just expand ~ and env vars
    s = os.path.expanduser(os.path.expandvars(s))
    return s


def prompt_for_path(processing_mode):
    """Prompt the user for a path using Rich input for robust paste behavior."""
    while True:
        if processing_mode == "single":
            raw = console.input(
                "[bold cyan]? [/][white]Enter the path to your video file[/]: ")
        else:
            raw = console.input(
                "[bold cyan]? [/][white]Enter the path to the directory containing videos[/]: "
            )

        path = _normalize_pasted_path(raw)
        if not path:
            console.print("[red]Please enter a non-empty path.[/]")
            continue

        if processing_mode == "single":
            if not os.path.exists(path) or not os.path.isfile(path):
                console.print(
                    "[red]File not found.[/] Please enter a valid path to a video file."
                )
                continue
        else:
            if not os.path.exists(path) or not os.path.isdir(path):
                console.print(
                    "[red]Directory not found.[/] Please enter a valid directory path."
                )
                continue

        return path


def prompt_percentage(prompt_text, default_value, min_value, max_value):
    """Prompt the user for a percentage value within bounds."""

    prompt_suffix = f" ({min_value}-{max_value}%)"
    while True:
        raw = Prompt.ask(
            f"{prompt_text}{prompt_suffix}",
            default=str(default_value),
            console=console,
            show_default=True,
        )
        raw = (raw or "").strip()

        if not raw:
            return float(default_value)

        if raw.endswith("%"):
            raw = raw[:-1].strip()

        try:
            value = float(raw)
        except ValueError:
            console.print("[red]Please enter a numeric value.[/]")
            continue

        if not (min_value <= value <= max_value):
            console.print(
                f"[red]Value must be between {min_value} and {max_value} percent.[/]"
            )
            continue

        return value


def main():
    """Main function."""
    try:
        console.print("[bold magenta]=== Video Watermarker ===[/]\n")

        processing_mode = questionary.select(
            "What would you like to watermark?",
            choices=[
                questionary.Choice(title="Single video", value="single"),
                questionary.Choice(
                    title="Directory of videos", value="directory"),
            ],
        ).ask()

        if processing_mode is None:
            console.print("\n[bold yellow]No option selected. Exiting.[/]")
            return

        target_path = prompt_for_path(processing_mode)

        console.print(
            "\nEnter watermark text (leave blank to skip a line). At least one line is required."
        )
        while True:
            line1 = console.input(
                "[bold cyan]? [/][white]Watermark text - Line 1 (optional)[/]: "
            ).strip()
            line2 = console.input(
                "[bold cyan]? [/][white]Watermark text - Line 2 (optional)[/]: "
            ).strip()
            if line1 or line2:
                break
            console.print(
                "[red]At least one line of text is required. Please try again.[/]\n")

        console.print(
            "\nCoverage controls how much screen area the text occupies; opacity controls transparency."
        )
        coverage_pct = prompt_percentage(
            "Watermark coverage percentage",
            default_value=50,
            min_value=1,
            max_value=100,
        )
        opacity_pct = prompt_percentage(
            "Watermark opacity percentage",
            default_value=15,
            min_value=0,
            max_value=100,
        )

        if processing_mode == "single":
            success = add_watermark_to_video(
                target_path, line1, line2, coverage_pct, opacity_pct
            )
            if success:
                console.print(
                    "\n[bold green]Watermarking completed successfully![/]")
            else:
                console.print("\n[bold red]Watermarking failed.[/]")
        else:  # directory mode
            success = process_directory(
                target_path, line1, line2, coverage_pct, opacity_pct
            )
            if success:
                console.print("\n[bold green]Batch watermarking completed![/]")
            else:
                console.print("\n[bold red]Batch watermarking failed.[/]")

    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]Operation cancelled by user.[/]")
    except Exception as e:
        console.print(f"\n[bold red]Error:[/] {str(e)}")


if __name__ == "__main__":
    main()
