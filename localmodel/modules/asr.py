"""百度语音识别（ASR）"""
import os
import time
from modules.config import baidu_client, logger
from modules.audio_utils import convert_audio_to_wav


def voice_to_text(audio_file: str | None) -> str:
    """百度语音识别，自动转换音频格式"""
    if audio_file is None:
        return '未收到音频'
    start_time = time.time()
    logger.info('开始语音识别...')
    try:
        wav_path = convert_audio_to_wav(audio_file)
        with open(wav_path, 'rb') as f:
            audio_data = f.read()
        os.unlink(wav_path)
        result = baidu_client.asr(audio_data, 'wav', 16000, {'dev_pid': 1537})
        elapsed = time.time() - start_time
        logger.info(f'语音识别完成，耗时 {elapsed:.2f} 秒，结果: {result}')
        if isinstance(result, dict) and result.get('err_no') == 0:
            return result['result'][0]
        else:
            error_msg = f'识别失败: {result.get("err_msg", "未知错误")}'
            logger.error(error_msg)
            return error_msg
    except Exception as e:
        logger.error(f'语音识别异常: {e}', exc_info=True)
        return f'错误: {e}'
