#!/usr/bin/env python3
"""
Simple Video Watermarker
Adds a centered two-line text watermark at ~10% opacity over the frame.
"""

import cv2
import numpy as np
import os
import math
from PIL import Image, ImageDraw, ImageFont
import inquirer

# Resolve paths relative to this script, not the current working directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def validate_video_path(answers, current):
    """Validate that the video file exists."""
    if not os.path.exists(current):
        raise inquirer.errors.ValidationError('', reason='File not found. Please enter a valid path.')
    return True


def validate_text_input(answers, current):
    """Validate that at least one line of text is provided."""
    line1 = answers.get('line1', '')
    line2 = current
    if not line1.strip() and not line2.strip():
        raise inquirer.errors.ValidationError('', reason='At least one line of text is required.')
    return True


def validate_directory_path(answers, current):
    """Validate that the directory exists."""
    if not os.path.exists(current) or not os.path.isdir(current):
        raise inquirer.errors.ValidationError('', reason='Directory not found. Please enter a valid directory path.')
    return True


def process_directory(directory_path, text_line1, text_line2):
    """Process all video files in a directory."""
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
    video_files = []
    
    # Find all video files in the directory
    for file in os.listdir(directory_path):
        if any(file.lower().endswith(ext) for ext in video_extensions):
            video_files.append(os.path.join(directory_path, file))
    
    if not video_files:
        print(f"\nNo video files found in directory: {directory_path}")
        return False
    
    print(f"\nFound {len(video_files)} video file(s) to process:")
    for i, video_file in enumerate(video_files, 1):
        print(f"{i}. {os.path.basename(video_file)}")
    
    print("\nProcessing videos...")
    successful = 0
    failed = 0
    
    for i, video_file in enumerate(video_files, 1):
        print(f"\n--- Processing video {i}/{len(video_files)}: {os.path.basename(video_file)} ---")
        success = add_watermark_to_video(video_file, text_line1, text_line2)
        if success:
            successful += 1
        else:
            failed += 1
    
    print(f"\n=== Batch Processing Complete ===")
    print(f"Successfully processed: {successful} videos")
    print(f"Failed: {failed} videos")
    
    return successful > 0


def get_unique_output_path(base_name):
    """Generate a unique output path by appending '_copy' if file already exists."""
    output_dir = os.path.join(SCRIPT_DIR, "output_videos")
    base_output_path = os.path.join(output_dir, f"{base_name}_watermarked.mp4")
    
    # If file doesn't exist, return the original path
    if not os.path.exists(base_output_path):
        return base_output_path
    
    # File exists, so we need to create a copy version
    counter = 1
    while True:
        if counter == 1:
            copy_path = os.path.join(output_dir, f"{base_name}_watermarked_copy.mp4")
        else:
            copy_path = os.path.join(output_dir, f"{base_name}_watermarked_copy{counter}.mp4")
        
        if not os.path.exists(copy_path):
            return copy_path
        
        counter += 1


def create_watermark_overlay(frame_width, frame_height, text_line1, text_line2):
    """Create a watermark overlay image with text."""
    # Create transparent image for watermark
    overlay = Image.new('RGBA', (frame_width, frame_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Use full screen for centering text
    watermark_width = frame_width
    watermark_height = frame_height
    
    # Determine font size up-front
    font_size = max(60, min((watermark_width // 5), (watermark_height // 6)))

    # Try common cross-platform font locations; fallback to default if none found
    font_candidates = [
        # macOS
        "/System/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        # Windows
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
    ]
    font = None
    for path in font_candidates:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, font_size)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()
    
    # Calculate text positioning
    # Get text dimensions
    bbox1 = draw.textbbox((0, 0), text_line1, font=font)
    bbox2 = draw.textbbox((0, 0), text_line2, font=font)
    
    text1_width = bbox1[2] - bbox1[0]
    text1_height = bbox1[3] - bbox1[1]
    text2_width = bbox2[2] - bbox2[0]
    text2_height = bbox2[3] - bbox2[1]
    
    # Center the text in the watermark area
    spacing = 10 if (text_line1.strip() and text_line2.strip()) else 0
    total_text_height = text1_height + text2_height + spacing
    start_y = (watermark_height - total_text_height) // 2
    
    # Position for line 1
    x1 = (watermark_width - text1_width) // 2
    y1 = start_y
    
    # Position for line 2
    x2 = (watermark_width - text2_width) // 2
    y2 = start_y + text1_height + spacing
    
    # Draw text with white color and 10% opacity
    text_color = (255, 255, 255, 26)  # White with alpha (10% of 255 = 26)
    draw.text((x1, y1), text_line1, font=font, fill=text_color)
    draw.text((x2, y2), text_line2, font=font, fill=text_color)
    
    return overlay


def add_watermark_to_video(video_path, text_line1, text_line2):
    """Add watermark to video and save the result."""
    # Open video
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return False
    
    # Get video properties (guard against 0/NaN values)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    if (isinstance(fps, float) and math.isnan(fps)) or fps <= 0:
        fps = 30.0
    total_frames = int((cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) or 0)
    
    print(f"\nVideo info:")
    print(f"Resolution: {frame_width}x{frame_height}")
    print(f"FPS: {fps}")
    print(f"Total frames: {total_frames}")
    
    # Create output filename with unique path handling
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_path = get_unique_output_path(base_name)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Define codec and create VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    if not out.isOpened():
        print("Error: Could not open VideoWriter with codec 'mp4v'.")
        cap.release()
        return False
    
    # Create watermark overlay once and prepare per-pixel alpha compositing
    watermark_overlay = create_watermark_overlay(frame_width, frame_height, text_line1, text_line2)
    overlay_rgba = np.array(watermark_overlay)
    overlay_bgr = cv2.cvtColor(overlay_rgba[:, :, :3], cv2.COLOR_RGB2BGR)
    overlay_alpha = (overlay_rgba[:, :, 3].astype(np.float32) / 255.0)
    # Optional global strength multiplier (1.0 uses overlay alpha as-is)
    strength = 1.0
    mask = np.clip(overlay_alpha * strength, 0.0, 1.0)
    
    print(f"\nProcessing video...")
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Per-pixel alpha blend the overlay onto the frame in BGR space
        frame_float = frame.astype(np.float32)
        overlay_float = overlay_bgr.astype(np.float32)
        # Blend each color channel using the same alpha mask
        for c in range(3):
            frame_float[:, :, c] = frame_float[:, :, c] * (1.0 - mask) + overlay_float[:, :, c] * mask
        final_frame = np.clip(frame_float, 0, 255).astype(np.uint8)
        
        # Write frame
        out.write(final_frame)
        
        frame_count += 1
        if total_frames > 0 and frame_count % 30 == 0:  # Progress update every 30 frames
            progress = (frame_count / total_frames) * 100
            print(f"Progress: {progress:.1f}%")
    
    # Release everything
    cap.release()
    out.release()
    
    print(f"\nWatermarked video saved as: {output_path}")
    return True


def _normalize_pasted_path(raw_path: str) -> str:
    if not isinstance(raw_path, str):
        return ""
    # Trim leading/trailing whitespace
    s = raw_path.strip()
    # Remove any surrounding quotes and any stray quote chars
    if (len(s) >= 2) and ((s[0] == s[-1]) and s[0] in ('"', "'")):
        s = s[1:-1]
    s = s.replace('"', '').replace("'", '')
    # Convert Finder-style escaped spaces to real spaces
    s = s.replace('\\ ', ' ')
    # Keep spaces in path; just expand ~ and env vars
    s = os.path.expanduser(os.path.expandvars(s))
    return s


def prompt_for_path(processing_mode: str) -> str:
    """Prompt the user for a path using standard input for robust paste behavior."""
    while True:
        if processing_mode == 'single':
            raw = input("[?] Enter the path to your video file: ")
        else:
            raw = input("[?] Enter the path to the directory containing videos: ")

        path = _normalize_pasted_path(raw)
        if not path:
            print("Please enter a non-empty path.")
            continue

        if processing_mode == 'single':
            if not os.path.exists(path) or not os.path.isfile(path):
                print("File not found. Please enter a valid path to a video file.")
                continue
        else:
            if not os.path.exists(path) or not os.path.isdir(path):
                print("Directory not found. Please enter a valid directory path.")
                continue

        return path


def main():
    """Main function."""
    try:
        print("=== Video Watermarker ===")
        print()
        
        # First, ask user what they want to process
        mode_question = [
            inquirer.List(
                'processing_mode',
                message='What would you like to watermark?',
                choices=[
                    ('Single video file', 'single'),
                    ('All videos in a directory', 'directory')
                ]
            )
        ]
        
        mode_answer = inquirer.prompt(mode_question)
        
        if not mode_answer:
            print("\nOperation cancelled by user.")
            return
        
        processing_mode = mode_answer['processing_mode']
        
        # Prompt for path via standard input (more robust for paste)
        target_path = prompt_for_path(processing_mode)

        # Prompt for watermark text using standard input as well
        # At least one of the two lines must be non-empty
        while True:
            line1 = input("[?] Enter watermark text - Line 1 (optional): ").strip()
            line2 = input("[?] Enter watermark text - Line 2 (optional): ").strip()
            if line1 or line2:
                break
            print("At least one line of text is required. Please try again.\n")
        
        # Process based on mode
        if processing_mode == 'single':
            success = add_watermark_to_video(target_path, line1, line2)
            if success:
                print("\nWatermarking completed successfully!")
            else:
                print("\nWatermarking failed.")
        else:  # directory mode
            success = process_directory(target_path, line1, line2)
            if success:
                print("\nBatch watermarking completed!")
            else:
                print("\nBatch watermarking failed.")
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nError: {str(e)}")


if __name__ == "__main__":
    main()
