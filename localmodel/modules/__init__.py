"""聊天机器人模块包"""
from .config import logger, avatar_img, restore_proxy, BASE_DIR, validate_config
from .model import chat_with_liuying_stream, load_model, request_stop, clear_stop_flag, is_stop_requested
from .asr import voice_to_text
from .tts import text_to_speech, save_voice, preload_common_audio, cleanup_old_voices
from .weather import get_weather_by_city, WEATHER_PATTERN
from .history import (
    load_history, save_history, delete_history,
    refresh_history_list, export_history, cleanup_old_histories,
)
from .ui import custom_css
