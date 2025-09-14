#!/usr/bin/env python3
"""
Simple Video Watermarker
Adds a two-line text watermark to videos with 30% opacity covering half the screen.
"""

import cv2
import numpy as np
import os
from PIL import Image, ImageDraw, ImageFont
import inquirer


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
    output_dir = "output_videos"
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
    
    # Try to use a system font, fallback to default if not available
    try:
        # Triple the previous font size for greater visibility
        font_size = max(60, min((watermark_width // 5), (watermark_height // 6)))
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
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
    total_text_height = text1_height + text2_height + 10  # 10px spacing
    start_y = (watermark_height - total_text_height) // 2
    
    # Position for line 1
    x1 = (watermark_width - text1_width) // 2
    y1 = start_y
    
    # Position for line 2
    x2 = (watermark_width - text2_width) // 2
    y2 = start_y + text1_height + 10
    
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
    
    # Get video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"\nVideo info:")
    print(f"Resolution: {frame_width}x{frame_height}")
    print(f"FPS: {fps}")
    print(f"Total frames: {total_frames}")
    
    # Create output filename with unique path handling
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_path = get_unique_output_path(base_name)
    
    # Create output directory if it doesn't exist
    os.makedirs("output_videos", exist_ok=True)
    
    # Define codec and create VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    
    # Create watermark overlay
    watermark_overlay = create_watermark_overlay(frame_width, frame_height, text_line1, text_line2)
    
    # Convert PIL image to OpenCV format
    watermark_cv = cv2.cvtColor(np.array(watermark_overlay), cv2.COLOR_RGBA2BGRA)
    
    print(f"\nProcessing video...")
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert frame to BGRA for alpha blending
        frame_bgra = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
        
        # Apply watermark with 10% opacity
        alpha = 0.1
        blended = cv2.addWeighted(frame_bgra, 1.0, watermark_cv, alpha, 0)
        
        # Convert back to BGR for video writer
        final_frame = cv2.cvtColor(blended, cv2.COLOR_BGRA2BGR)
        
        # Write frame
        out.write(final_frame)
        
        frame_count += 1
        if frame_count % 30 == 0:  # Progress update every 30 frames
            progress = (frame_count / total_frames) * 100
            print(f"Progress: {progress:.1f}%")
    
    # Release everything
    cap.release()
    out.release()
    
    print(f"\nWatermarked video saved as: {output_path}")
    return True


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
        
        # Get path based on mode
        if processing_mode == 'single':
            path_questions = [
                inquirer.Path(
                    'target_path',
                    message='Enter the path to your video file',
                    path_type=inquirer.Path.FILE,
                    validate=validate_video_path,
                    exists=True
                )
            ]
        else:  # directory mode
            path_questions = [
                inquirer.Path(
                    'target_path',
                    message='Enter the path to the directory containing videos',
                    path_type=inquirer.Path.DIRECTORY,
                    validate=validate_directory_path,
                    exists=True
                )
            ]
        
        # Get watermark text
        text_questions = [
            inquirer.Text(
                'line1',
                message='Enter watermark text - Line 1',
                default=''
            ),
            inquirer.Text(
                'line2',
                message='Enter watermark text - Line 2',
                default='',
                validate=validate_text_input
            )
        ]
        
        # Combine path and text questions
        all_questions = path_questions + text_questions
        answers = inquirer.prompt(all_questions)
        
        if not answers:
            print("\nOperation cancelled by user.")
            return
        
        target_path = answers['target_path']
        line1 = answers['line1'].strip()
        line2 = answers['line2'].strip()
        
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
