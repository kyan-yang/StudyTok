from moviepy.editor import VideoFileClip
import os

def convert_mov_to_mp4(input_path, output_path):
    # Load the .mov file
    video_clip = VideoFileClip(input_path)
    
    # Write the video file to .mp4 format with audio, using a faster preset
    video_clip.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        ffmpeg_params=['-preset', 'fast', '-crf', '23', '-threads', '4']
    )

# Example usage
os.chdir(r'C:\Users\Kyan\Desktop\McHack\assets\media')
input_path = "clip1.mov"
output_path = "output.mp4"
convert_mov_to_mp4(input_path, output_path)