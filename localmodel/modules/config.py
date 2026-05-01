"""环境变量、路径、全局常量"""
import os
import base64
import logging
from pathlib import Path
from dotenv import load_dotenv
from aip import AipSpeech

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

os.environ['NO_PROXY'] = '*'

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# FFmpeg
FFMPEG_PATH = os.getenv('FFMPEG_PATH')
if FFMPEG_PATH:
    os.environ["PATH"] = FFMPEG_PATH + os.pathsep + os.environ.get("PATH", "")

# 百度语音
APP_ID = os.getenv('BAIDU_APP_ID')
API_KEY = os.getenv('BAIDU_API_KEY')
SECRET_KEY = os.getenv('BAIDU_SECRET_KEY')
baidu_client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

# Fish Audio
FISH_API_KEY = os.getenv('FISH_API_KEY')
LIUYING_REFERENCE_ID = os.getenv('LIUYING_REFERENCE_ID')
PROXY_URL = os.getenv('PROXY_URL')

# 模型路径
MODEL_PATH = str(BASE_DIR / 'models' / 'qwen' / 'Qwen2-7B-Instruct')

# 数据目录
HISTORY_DIR = str(BASE_DIR / 'histories')
os.makedirs(HISTORY_DIR, exist_ok=True)

VOICES_DIR = BASE_DIR / 'voices'
VOICES_DIR.mkdir(exist_ok=True)

# 头像
def _load_avatar() -> str:
    avatar_path = BASE_DIR / 'liuying_avatar.png'
    if avatar_path.exists():
        with open(avatar_path, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode()
        return f'data:image/png;base64,{img_data}'
    return 'https://picsum.photos/id/104/120/120'

avatar_img = _load_avatar()

# 代理环境变量暂存（启动时弹出，退出时还原）
_saved_proxy: dict[str, str] = {}
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    if key in os.environ:
        _saved_proxy[key] = os.environ.pop(key)


def restore_proxy():
    """恢复暂存的代理环境变量"""
    for key, value in _saved_proxy.items():
        os.environ[key] = value


def validate_config():
    """检查关键配置，缺失项打印警告但不阻塞启动"""
    checks = {
        '百度语音 (ASR)': all([APP_ID, API_KEY, SECRET_KEY]),
        'Fish Audio (TTS)': all([FISH_API_KEY, LIUYING_REFERENCE_ID]),
        '本地模型路径': os.path.exists(MODEL_PATH) if MODEL_PATH else False,
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        logger.warning(f'以下配置缺失或无效: {", ".join(missing)}')
        logger.warning('缺失的服务将在对应功能使用时提示错误，不影响其他功能')
    else:
        logger.info('所有配置检查通过')
