import subprocess
import glob
import os
from concurrent.futures import ProcessPoolExecutor
from moviepy.editor import VideoFileClip, CompositeVideoClip, concatenate_videoclips
from moviepy.video.fx.all import mask_color
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

# Constants
FFMPEG_DIRECTORY = os.path.abspath('ffmpeg/bin/ffmpeg.exe')
CHROMA_KEY = "chroma_key/chroma_key.mp4"
BLUR_AMOUNT = "boxblur=10:5"
OUTPUT_DIR = "result"
TEMP_DIR = "temp"

# Ensure output and temp directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def create_blurred_background(input_video: str) -> VideoFileClip:
    blurred_background_path = os.path.join(TEMP_DIR, f"{os.path.basename(input_video)[:-4]}_temp.mp4")
    cmd = [
        FFMPEG_DIRECTORY, '-i', input_video,
        '-vf', BLUR_AMOUNT,
        '-s', '1080x1920', 
        '-r', '24', 
        '-loglevel', 'error',
        '-hide_banner',
        '-y'
        blurred_background_path
    ]
    subprocess.run(cmd, check=True)
    return VideoFileClip(blurred_background_path)

def process_video(input_video: str) -> None:
    logger.info(f'Starting video: {input_video}')

    blurred_background_clip = create_blurred_background(input_video)

    with VideoFileClip(input_video) as clip, VideoFileClip(CHROMA_KEY) as chroma_key_clip:
        resized_clip = clip.resize(width=1080)

        chroma_key_duration = chroma_key_clip.duration

        trimmed_resized_clip = resized_clip.subclip(0, min(chroma_key_duration, resized_clip.duration))

        blurred_background_clip = blurred_background_clip.set_duration(chroma_key_duration)

        chroma_key_clip = chroma_key_clip.resize(newsize=(1080, 1920))

        masked_chroma_key = mask_color(chroma_key_clip, color=[35, 177, 77], thr=83, s=15)

        trimmed_resized_clip = trimmed_resized_clip.set_fps(24)
        masked_chroma_key = masked_chroma_key.set_fps(24)

        final_clip = CompositeVideoClip([
            blurred_background_clip.set_duration(masked_chroma_key.duration),
            trimmed_resized_clip.set_position("center"),
            masked_chroma_key.set_position("center")
        ])

        output_video_path = os.path.join(OUTPUT_DIR, f"{os.path.basename(input_video)[:-4]}_complete.mp4")

        final_clip.write_videofile(
            output_video_path,
            codec='libvpx-vp9',
            fps=24,
            preset='fast', 
            logger=None,
            threads=8
        )

        logger.info(f'Video processed: {input_video}')

    blurred_background_clip.close()

def render_videos(input_video_paths: list) -> None:
    cores = int(input('Number cores: '))
    print()

    with ProcessPoolExecutor(max_workers=cores) as executor:
        executor.map(process_video, input_video_paths)

if __name__ == "__main__":
    print('Developer - https://t.me/daniilprg\n')
    input_video_paths = glob.glob("original_videos/*.mp4")
    render_videos(input_video_paths)
