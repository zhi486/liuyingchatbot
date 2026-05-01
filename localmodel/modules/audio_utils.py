"""音频格式转换"""
import tempfile
from pydub import AudioSegment


def convert_audio_to_wav(input_path: str) -> str:
    """将任意音频转换为 16kHz 单声道 WAV，返回临时文件路径"""
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_path = f.name
    audio.export(temp_path, format='wav')
    return temp_path
