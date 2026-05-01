"""Fish Audio 文本转语音（TTS）"""
import os
import time
import tempfile
import shutil
import requests
from datetime import datetime
from modules.config import FISH_API_KEY, LIUYING_REFERENCE_ID, PROXY_URL, VOICES_DIR, logger

_audio_cache: dict[str, str] = {}

TTS_URL = 'https://api.fish.audio/v1/tts'
TTS_HEADERS = {
    'Authorization': f'Bearer {FISH_API_KEY}',
    'Content-Type': 'application/json',
}
TTS_PROXIES = {'http': PROXY_URL, 'https': PROXY_URL}
MAX_RETRIES = 2


def text_to_speech(text: str) -> str | None:
    """文本转语音，带缓存和重试"""
    if text in _audio_cache:
        cached_path = _audio_cache[text]
        if os.path.exists(cached_path):
            logger.info(f'语音缓存命中: {text[:30]}...')
            return cached_path
        del _audio_cache[text]

    start_total = time.time()
    logger.info(f'开始语音合成: {text[:30]}...')
    payload = {'text': text, 'reference_id': LIUYING_REFERENCE_ID, 'format': 'mp3'}

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(TTS_URL, headers=TTS_HEADERS, json=payload, proxies=TTS_PROXIES, timeout=15)
            if resp.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                    f.write(resp.content)
                    temp_path = f.name
                _audio_cache[text] = temp_path
                logger.info(f'语音合成完成，总耗时 {time.time() - start_total:.2f} 秒')
                return temp_path
            else:
                logger.warning(f'Fish Audio 请求失败 ({resp.status_code})，尝试 {attempt+1}/{MAX_RETRIES}')
        except Exception as e:
            logger.warning(f'Fish Audio 异常，尝试 {attempt+1}/{MAX_RETRIES}: {e}')
            if attempt == MAX_RETRIES - 1:
                logger.error(f'语音合成最终失败: {e}', exc_info=True)
                return None
            time.sleep(1)
    return None


def save_voice(text: str) -> str | None:
    """保存语音到持久目录"""
    audio_path = text_to_speech(text)
    if audio_path and os.path.exists(audio_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'voice_{timestamp}_{hash(text) % 10000}.mp3'
        save_path = VOICES_DIR / filename
        shutil.copy2(audio_path, save_path)
        logger.info(f'语音已保存至: {save_path}')
        return str(save_path)
    return None


def preload_common_audio():
    """预生成常用回复语音"""
    COMMON_RESPONSES = [
        '你好', '嗯……', '是的', '不是呢', '谢谢', '再见',
        '今天天气真好呢', '嗯，我明白了', '有点不太想提', '要尝尝橡木蛋糕卷吗？',
    ]
    logger.info('开始预生成常用语音...')
    for text in COMMON_RESPONSES:
        if text not in _audio_cache:
            try:
                audio_path = text_to_speech(text)
                if audio_path:
                    logger.info(f'预生成成功: {text}')
                else:
                    logger.warning(f'预生成失败: {text}')
            except Exception as e:
                logger.error(f'预生成异常 {text}: {e}')
    logger.info('预生成完成')


def cleanup_old_voices(max_age_days: int = 30):
    """删除超过 max_age_days 天的语音文件"""
    cutoff = time.time() - max_age_days * 86400
    count = 0
    for f in VOICES_DIR.glob('*.mp3'):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
                count += 1
        except OSError:
            pass
    if count:
        logger.info(f'已清理 {count} 个过期语音文件')
