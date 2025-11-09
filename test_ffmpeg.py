from modules.ffmpeg_utils import mux_audio_into_video
print(mux_audio_into_video("in.mp4", "tts.mp3", out_path="out.mp4", keep_original_audio=True))
