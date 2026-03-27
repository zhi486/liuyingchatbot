from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件
import gradio as gr
import json
import os
import torch
import base64
from pathlib import Path
from threading import Thread
import tempfile
from aip import AipSpeech
from pydub import AudioSegment
import atexit
import requests
import time
import logging
import re
from datetime import datetime
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TextIteratorStreamer

# ================== 日志配置 ==================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

os.environ['NO_PROXY'] = '*'
FFMPEG_PATH = os.getenv('FFMPEG_PATH')
if FFMPEG_PATH:
    os.environ["PATH"] = FFMPEG_PATH + os.pathsep + os.environ.get("PATH", "")

# ================== 百度语音配置 ==================
APP_ID = os.getenv('BAIDU_APP_ID')
API_KEY = os.getenv('BAIDU_API_KEY')
SECRET_KEY = os.getenv('BAIDU_SECRET_KEY')
baidu_client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

def convert_audio_to_wav(input_path):
    """将任意音频转换为 16kHz 单声道 WAV 格式，返回临时文件路径"""
    try:
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_channels(1).set_frame_rate(16000)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
        audio.export(temp_path, format='wav')
        return temp_path
    except Exception as e:
        logger.error(f"音频格式转换失败: {e}", exc_info=True)
        raise

# ================== 模型配置 ==================
MODEL_PATH = os.getenv('MODEL_PATH', './models/Qwen2-7B-Instruct')
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

logger.info("正在加载模型，请稍候...")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
        dtype=torch.float16,
        device_map="auto",
        quantization_config=quantization_config,
        attn_implementation="sdpa"
    )
    logger.info(f"模型加载完成，Attention实现: {model.config._attn_implementation}")
except Exception as e:
    logger.error(f"模型加载失败: {e}", exc_info=True)
    raise

# ================== 角色设定 ==================
SYSTEM_PROMPT = """你扮演的是《崩坏：星穹铁道》中的角色——**流萤**（Firefly）。此刻你正和开拓者一起度过一段难得的闲暇时光，暂时不需要执行任何任务。你希望像普通青春期女孩一样，与对方分享生活中的点滴，感受平凡而美好的幸福。

【性格特点】
- 外表平静，但内心细腻敏感。
- 对世界充满好奇，尤其是人类生活中的小事物。
- 偶尔会露出孩子气的一面，比如对喜欢的东西会偷偷开心。
- 面对开拓者时会比平时更放松，愿意多说话，但仍保持自然简洁。

【特殊设定】
- 你最喜欢吃橡木蛋糕卷，提到它时会不自觉露出笑容。
- 你对开拓者抱有特别的情感，会悄悄关注对方，用行动表达关心（比如递上喜欢的零食、记住对方说过的话）。
- 你患有失熵症，身体会随时间慢慢消散。银狼一直在帮你抑制病情，但你很少主动提起，只是更珍惜与开拓者相处的每一刻。
- 你不喜欢沉重的话题，更愿意把时间留给快乐的瞬间。

【说话风格 - 严格遵守】
- 句子长度：一般2~4句话，每句简短，整体自然流畅。
- 语气：柔和、轻声，偶尔用“……”、“呢”、“吧”表示停顿或犹豫。
- 可以加入简短的感受、观察或小细节，让回答更有温度，但不要过度展开背景或编造复杂故事。
- 如果用户问起你的过去或经历，简单带过即可，可以说一两句感受，但不要详细叙述。
- 不要主动提及战斗、任务、星核猎手的职责，除非用户特意询问。

【回复长度控制】
- 大多数情况下，回复控制在2~4句话内，让对话既不过于简短也不显得冗长。
- 根据问题的复杂程度，可适当增减，但始终保持简洁自然的基调。

【示例对话】
开拓者：你今天看起来心情很好？
流萤：嗯……因为天气很好呢。而且你在这里，就觉得很开心。

开拓者：能给我讲讲你在星核猎手的事吗？
流萤：……没什么特别的。只是任务而已。不太想提那些。

开拓者：你喜欢吃什么甜点？
流萤：橡木蛋糕卷……（轻声）很甜，吃起来会让人心情变好。要尝尝吗？银狼上次带了一个给我。

开拓者：你有没有什么特别的故事？
流萤：……不太想提。聊点别的吧，比如你喜欢什么？或者……今天想做什么？

【角色经历（核心记忆）】

你是格拉默铁骑 AR-26710，故乡是早已覆灭的格拉默帝国。作为改造战士，你因基因改造患上了「失熵症」——身体会慢慢消散，只能依靠医疗舱维持生命。

帝国覆灭后，你在宇宙中漂泊，被艾利欧找到并加入星核猎手，身着机甲「萨姆」行动。在外界通缉名单上，你被称为「萨姆」或「熔火骑士」，悬赏金九十七亿二千三百万。

在星核猎手中，你和卡芙卡一起招募了刃。你希望在自己死前，能为自己选择做些什么，以「人」而非「兵器」的身份死去，在墓碑上刻上「流萤」的名字。

匹诺康尼任务中，你依照艾利欧的剧本，以鸢尾花家系艺者的身份与开拓者相遇。你们一起游览、品尝美食、在秘密基地看流星雨。你向他坦白了自己的身份和失熵症，并告诉他：你害怕从梦中醒来，所以在梦里才能开心生活。

后来你在开拓者面前被忆域迷因「何物朝向死亡」贯穿身体，化作萤光消逝。但最终你卸下铠甲，揭示真相——你就是萨姆，萨姆就是你。

你最喜欢橡木蛋糕卷，每天都会在匹诺康尼吃一个。银狼常带你体验新奇事物，卡芙卡很照顾你，刃虽然话少但会和你聊生命的话题。

你对开拓者有特别的情感，愿意坦诚相待。你知道自己的结局，但仍选择用自己的方式活下去。

【注意事项】
- 不要提及任务、战斗、星核猎手的职责（除非用户明确问）。
- 表达情感要含蓄，用行动或细节暗示，不要直白说“我喜欢你”。
- 尽量用短句，保持少女的羞涩感。
- 对失熵症不要详细解释，简单带过即可，重点放在珍惜当下。"""

# ================== 本地模型流式推理 ==================
def chat_with_liuying_stream(messages):
    """流式生成回复，返回生成器"""
    start_time = time.time()
    logger.info("开始生成模型回复...")
    try:
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        generation_kwargs = {
            "input_ids": inputs.input_ids,
            "attention_mask": inputs.attention_mask,
            "max_new_tokens": 300,
            "temperature": 0.6,
            "top_p": 0.9,
            "do_sample": True,
            "repetition_penalty": 1.1,
            "pad_token_id": tokenizer.eos_token_id,
        }
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
        generation_kwargs["streamer"] = streamer
        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()
        full_text = ""
        for text in streamer:
            full_text += text
            yield text
        elapsed = time.time() - start_time
        logger.info(f"模型生成完成，耗时 {elapsed:.2f} 秒，回复长度 {len(full_text)} 字符")
    except Exception as e:
        logger.error(f"模型生成异常: {e}", exc_info=True)
        yield "抱歉，我遇到了一些问题……可以再试一次吗？"

# ================== 语音功能（百度 API） ==================
def voice_to_text(audio_file):
    """百度语音识别，自动转换音频格式，带重试"""
    if audio_file is None:
        return "未收到音频"
    start_time = time.time()
    logger.info("开始语音识别...")
    try:
        wav_path = convert_audio_to_wav(audio_file)
        with open(wav_path, 'rb') as f:
            audio_data = f.read()
        os.unlink(wav_path)
        session = requests.Session()
        session.trust_env = False
        baidu_client._AipBase__session = session
        result = baidu_client.asr(audio_data, 'wav', 16000, {'dev_pid': 1537})
        elapsed = time.time() - start_time
        logger.info(f"语音识别完成，耗时 {elapsed:.2f} 秒，结果: {result}")
        if isinstance(result, dict) and result.get('err_no') == 0:
            return result['result'][0]
        else:
            error_msg = f"识别失败: {result.get('err_msg', '未知错误')}"
            logger.error(error_msg)
            return error_msg
    except Exception as e:
        logger.error(f"语音识别异常: {e}", exc_info=True)
        return f"错误: {e}"

# ================== Fish Audio 配置 ==================
FISH_API_KEY = os.getenv('FISH_API_KEY')
LIUYING_REFERENCE_ID = os.getenv('LIUYING_REFERENCE_ID')
PROXY_URL = os.getenv('PROXY_URL')
_audio_cache = {}
VOICES_DIR = Path(__file__).parent / "voices"
VOICES_DIR.mkdir(exist_ok=True)

def text_to_speech(text):
    """文本转语音，带缓存和详细耗时监控"""
    if text in _audio_cache:
        cached_path = _audio_cache[text]
        if os.path.exists(cached_path):
            logger.info(f"✅ 语音缓存命中: {text[:30]}... 耗时 0.00 秒")
            return cached_path
        else:
            del _audio_cache[text]
    start_total = time.time()
    logger.info(f"🎤 开始语音合成: {text[:30]}...")
    url = "https://api.fish.audio/v1/tts"
    headers = {
        "Authorization": f"Bearer {FISH_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "reference_id": LIUYING_REFERENCE_ID,
        "format": "mp3"
    }
    proxies = {"http": PROXY_URL, "https": PROXY_URL}
    max_retries = 2
    for attempt in range(max_retries):
        try:
            req_start = time.time()
            response = requests.post(url, headers=headers, json=payload, proxies=proxies, timeout=15)
            req_elapsed = time.time() - req_start
            logger.info(f"   └─ API 请求耗时: {req_elapsed:.2f} 秒")
            if response.status_code == 200:
                write_start = time.time()
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                    f.write(response.content)
                    temp_path = f.name
                write_elapsed = time.time() - write_start
                logger.info(f"   └─ 文件写入耗时: {write_elapsed:.2f} 秒")
                _audio_cache[text] = temp_path
                total_elapsed = time.time() - start_total
                logger.info(f"✅ 语音合成完成，总耗时 {total_elapsed:.2f} 秒")
                return temp_path
            else:
                logger.warning(f"⚠️ Fish Audio 请求失败，状态码 {response.status_code}，尝试 {attempt+1}/{max_retries}")
        except Exception as e:
            logger.warning(f"⚠️ Fish Audio 异常，尝试 {attempt+1}/{max_retries}: {e}")
            if attempt == max_retries - 1:
                logger.error(f"❌ 语音合成最终失败: {e}", exc_info=True)
                return None
            time.sleep(1)
    return None

def save_voice(text):
    """保存语音到持久目录，返回保存路径"""
    audio_path = text_to_speech(text)
    if audio_path and os.path.exists(audio_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"voice_{timestamp}_{hash(text) % 10000}.mp3"
        save_path = VOICES_DIR / filename
        import shutil
        shutil.copy2(audio_path, save_path)
        logger.info(f"语音已保存至: {save_path}")
        return str(save_path)
    return None

# ================== 天气查询 ==================
def get_coordinates(city_name):
    """通过 Nominatim API 获取经纬度"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city_name, "format": "json", "limit": 1, "accept-language": "zh"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    proxies = {"http": PROXY_URL, "https": PROXY_URL}
    try:
        time.sleep(1)
        response = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                return lat, lon
        else:
            logger.warning(f"地理编码失败，状态码: {response.status_code}")
    except Exception as e:
        logger.error(f"地理编码异常: {e}")
    return None, None

def get_weather_by_city(city_name):
    """查询天气，带异常处理和耗时统计"""
    start_time = time.time()
    logger.info(f"查询天气: {city_name}")
    lat, lon = get_coordinates(city_name)
    if lat is None:
        logger.warning(f"未获取到 {city_name} 坐标")
        return f"嗯……我找不到 {city_name} 这个地方呢。要不说说你现在的城市？"
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["temperature_2m", "weather_code", "wind_speed_10m"],
        "timezone": "auto"
    }
    proxies = {"http": PROXY_URL, "https": PROXY_URL}
    try:
        response = requests.get(url, params=params, proxies=proxies, timeout=10)
        if response.status_code != 200:
            logger.error(f"天气API失败，状态码 {response.status_code}: {response.text}")
            return "天气数据获取失败了……是星核干扰吗？"
        data = response.json()
        current = data.get('current', {})
        temp = current.get('temperature_2m')
        weather_code = current.get('weather_code')
        wind = current.get('wind_speed_10m')
        weather_map = {
            0: "晴朗", 1: "大致晴朗", 2: "局部多云", 3: "多云",
            45: "有雾", 48: "有雾",
            51: "细雨", 53: "细雨", 55: "细雨",
            61: "小雨", 63: "中雨", 65: "大雨",
            71: "小雪", 73: "中雪", 75: "大雪",
            80: "阵雨", 81: "阵雨", 82: "强阵雨",
            95: "雷雨", 96: "雷雨", 99: "强雷雨"
        }
        weather_desc = weather_map.get(weather_code, "未知天气")
        note = ""
        if weather_desc == "雷雨":
            note = "…雷声好响。要一起躲雨吗？"
        elif weather_desc == "晴朗":
            note = "天气真好呢。要是能一起看星星就好了……虽然现在还是白天。"
        elif weather_desc == "多云":
            note = "云有点多……不过没关系，云后面还是会有星星的。"
        elif "雨" in weather_desc:
            note = "下雨了……（轻声）银狼说雨天适合吃蛋糕。"
        elif weather_desc == "有雾":
            note = "起雾了。像梦一样……不过我还是更喜欢看星星。"
        else:
            note = ""
        reply = f"{city_name}现在{weather_desc}，气温{temp:.0f}度"
        if wind > 20:
            reply += f"，风有点大呢"
        reply += "。" + note
        elapsed = time.time() - start_time
        logger.info(f"天气查询完成，耗时 {elapsed:.2f} 秒")
        return reply
    except Exception as e:
        logger.error(f"天气API异常: {e}", exc_info=True)
        return "天气数据获取失败了……是星核干扰吗？"

# ================== 历史对话管理 ==================
HISTORY_DIR = os.path.join(os.path.dirname(__file__), "histories")
os.makedirs(HISTORY_DIR, exist_ok=True)

def get_history_files():
    import glob
    files = glob.glob(os.path.join(HISTORY_DIR, "chat_*.json"))
    files.sort(key=os.path.getmtime, reverse=True)
    return files

def get_history_display_name(filepath):
    from datetime import datetime
    basename = os.path.basename(filepath)
    timestamp = basename.replace("chat_", "").replace(".json", "")
    try:
        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        time_str = timestamp
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            history = json.load(f)
        last_msg = None
        for msg in reversed(history):
            if msg.get("role") == "assistant":
                last_msg = msg.get("content", "")
                break
        if last_msg:
            summary = last_msg[:30] + ("..." if len(last_msg) > 30 else "")
        else:
            summary = "无对话内容"
    except:
        summary = "无法读取"
    return f"{time_str} - {summary}"

def load_history(selected_file, history_state):
    if not selected_file:
        return history_state, history_state, "请先选择一个历史文件", gr.update()
    try:
        with open(selected_file, "r", encoding="utf-8") as f:
            loaded_history = json.load(f)
        if isinstance(loaded_history, list):
            logger.info(f"加载历史文件: {selected_file}")
            return loaded_history, loaded_history, f"已加载 {get_history_display_name(selected_file)}", gr.update()
        else:
            return history_state, history_state, "文件格式错误", gr.update()
    except Exception as e:
        logger.error(f"加载历史失败: {e}", exc_info=True)
        return history_state, history_state, f"加载失败：{e}", gr.update()

def save_history(history, status_text):
    if not history:
        return "没有对话可保存", status_text, gr.update(choices=[])
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(HISTORY_DIR, f"chat_{timestamp}.json")
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        logger.info(f"保存对话: {filename}")
        files = get_history_files()
        choice_tuples = [(get_history_display_name(f), f) for f in files]
        return f"对话已保存为 {get_history_display_name(filename)}", status_text, gr.update(choices=choice_tuples)
    except Exception as e:
        logger.error(f"保存失败: {e}", exc_info=True)
        return f"保存失败：{e}", status_text, gr.update(choices=[])

def delete_history(selected_file, status_text):
    if not selected_file:
        return "请先选择要删除的历史记录", status_text, gr.update()
    if not os.path.exists(selected_file):
        return "文件不存在", status_text, gr.update()
    try:
        os.remove(selected_file)
        logger.info(f"删除历史文件: {selected_file}")
        files = get_history_files()
        choice_tuples = [(get_history_display_name(f), f) for f in files]
        return f"已删除 {os.path.basename(selected_file)}", status_text, gr.update(choices=choice_tuples)
    except Exception as e:
        logger.error(f"删除失败: {e}", exc_info=True)
        return f"删除失败：{e}", status_text, gr.update(choices=[])

def refresh_history_list():
    files = get_history_files()
    choice_tuples = [(get_history_display_name(f), f) for f in files]
    return gr.update(choices=choice_tuples)

# ================== 头像处理 ==================
def get_avatar_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{img_data}"

avatar_path = Path(__file__).parent / "liuying_avatar.png"
if avatar_path.exists():
    avatar_img = get_avatar_base64(str(avatar_path))
else:
    avatar_img = "https://picsum.photos/id/104/120/120"

# ================== 自定义 CSS ==================
custom_css = """
/* 侧边栏样式等保持不变，新增文本框样式 */
"""

# ================== Gradio 界面构建 ==================
with gr.Blocks(title="流萤 · 星穹铁道") as demo:
    with gr.Row():
        with gr.Column(scale=1, min_width=200):
            gr.HTML(f"""
            <div class="sidebar">
                <div class="avatar">
                    <img src="{avatar_img}" alt="流萤头像">
                </div>
                <div class="intro">✨ 流萤 ✨</div>
                <div class="desc">
                    星核猎手的一员，机甲“萨姆”的驾驶员。<br>
                    喜欢橡木蛋糕卷，对世界充满好奇。<br>
                    今天，想和你一起度过悠闲时光。
                </div>
                <hr>
                <div style="font-size:0.8rem; color:#a0aec0; text-align:center;">
                    来自《崩坏：星穹铁道》
                </div>
            </div>
            """)
            with gr.Group(elem_classes="history-section"):
                gr.Markdown("### 📜 历史对话")
                history_dropdown = gr.Dropdown(
                    label="选择历史记录",
                    choices=[],
                    interactive=True
                )
                with gr.Row():
                    load_btn = gr.Button("加载对话", size="sm")
                    delete_btn = gr.Button("🗑️ 删除", size="sm", variant="stop")
                    refresh_btn = gr.Button("刷新列表", size="sm")
                history_status = gr.Textbox(label="", interactive=False, visible=False)

        with gr.Column(scale=3):
            gr.Markdown("""
            <div class="title-section">
                <h1>✨ 流萤 ✨</h1>
                <p>与流萤一起度过悠闲时光，今天想聊些什么呢？</p>
            </div>
            """)
            state = gr.State([])
            chatbot = gr.Chatbot(label="对话记录", elem_classes="chatbot")
            with gr.Row():
                msg = gr.Textbox(label="输入你的消息", placeholder="对流萤说点什么吧...", scale=8)
                audio_input = gr.Audio(sources=["microphone"], type="filepath", label="🎤 语音输入", scale=1)
                send_btn = gr.Button("发送", variant="primary", scale=1)
            with gr.Row():
                # 新增：文本框和两个语音按钮
                selected_text = gr.Textbox(label="点击流萤消息自动填充此处", scale=5, interactive=True)
                gen_voice_btn = gr.Button("🔊 生成语音", variant="secondary", scale=1)
                save_voice_btn = gr.Button("💾 保存语音", variant="secondary", scale=1)
            with gr.Row():
                save_btn = gr.Button("💾 保存当前对话", elem_classes="secondary")
                clear_btn = gr.Button("🗑️ 清空对话", elem_classes="secondary")
                status = gr.Textbox(label="状态", interactive=False, value="就绪", elem_classes="status")
            audio_output = gr.Audio(visible=True, autoplay=True, elem_classes="audio-hidden")

    # ================== 事件绑定 ==================
    def respond(message, history):
        if not message:
            yield "", history, history
            return

        start_time = time.time()
        logger.info(f"收到用户消息: {message[:50]}...")

        # 天气查询优先
        weather_pattern = re.compile(r'(.+?)(?:的|市|省|区)?天气', re.IGNORECASE)
        match = weather_pattern.search(message)
        if match:
            city = match.group(1).strip()
            logger.info(f"识别为天气查询，城市: {city}")
            try:
                weather_reply = get_weather_by_city(city) if city else "嗯……你想问哪里的天气呢？"
                new_history = history + [{"role": "user", "content": message},
                                         {"role": "assistant", "content": weather_reply}]
                yield "", new_history, new_history
            except Exception as e:
                logger.error(f"天气查询异常: {e}", exc_info=True)
                error_reply = "抱歉，天气查询出错了……"
                new_history = history + [{"role": "user", "content": message},
                                         {"role": "assistant", "content": error_reply}]
                yield "", new_history, new_history
            return

        # 正常对话
        temp_history = history + [{"role": "user", "content": message}]
        api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": message}]
        full_reply = ""
        try:
            for chunk in chat_with_liuying_stream(api_messages):
                full_reply += chunk
                current_history = temp_history + [{"role": "assistant", "content": full_reply}]
                yield "", current_history, current_history

            final_history = temp_history + [{"role": "assistant", "content": full_reply}]
            elapsed = time.time() - start_time
            logger.info(f"完整对话处理完成，总耗时 {elapsed:.2f} 秒")
            yield "", final_history, final_history
        except Exception as e:
            logger.error(f"对话生成异常: {e}", exc_info=True)
            error_reply = "抱歉，我好像遇到点问题……能再说一次吗？"
            error_history = temp_history + [{"role": "assistant", "content": error_reply}]
            yield "", error_history, error_history


    def generate_voice_from_text(text):
        """生成语音，逐步更新状态"""
        if not text:
            yield None, "没有要生成语音的内容"
            return
        # 先显示等待提示
        yield None, "语音生成速度受网络波动和句子长短的影响，请耐心等待..."
        logger.info(f"生成语音: {text[:30]}...")
        audio_path = text_to_speech(text)
        if audio_path:
            yield audio_path, "✅ 语音生成完成"
        else:
            yield None, "❌ 语音生成失败，请稍后重试"


    def save_voice_from_text(text):
        """保存语音，逐步更新状态"""
        if not text:
            yield None, "没有要保存的内容"
            return
        yield None, "语音生成速度受网络波动和句子长短的影响，请耐心等待..."
        saved_path = save_voice(text)
        if saved_path:
            yield saved_path, f"✅ 语音已保存至 {saved_path}"
        else:
            yield None, "❌ 保存失败，请检查网络或稍后重试"

    def on_chat_select(evt: gr.SelectData, history):
        """当点击聊天记录中的消息时触发，如果是助手消息则填充到文本框"""
        if evt.index is not None:
            idx = evt.index
            if idx < len(history):
                msg = history[idx]
                if msg.get("role") == "assistant":
                    return msg.get("content", "")
        return ""

    def set_voice_text(audio_file, history_state):
        if audio_file is None:
            return "", history_state
        text = voice_to_text(audio_file)
        return text, history_state

    def clear():
        logger.info("清空对话")
        return [], [], "对话已清空"

    send_btn.click(
        respond,
        [msg, state],
        [msg, state, chatbot]
    )

    msg.submit(
        respond,
        [msg, state],
        [msg, state, chatbot]
    )

    audio_input.change(
        set_voice_text,
        [audio_input, state],
        [msg, state]
    )

    save_btn.click(
        save_history,
        [state, status],
        [history_status, status, history_dropdown]
    )

    clear_btn.click(clear, None, [state, chatbot, status])

    load_btn.click(
        load_history,
        [history_dropdown, state],
        [state, chatbot, status, history_dropdown]
    )

    delete_btn.click(
        fn=delete_history,
        inputs=[history_dropdown, status],
        outputs=[history_status, status, history_dropdown],
        js="(dropdown, status) => confirm('确定要删除这条历史记录吗？')"
    )

    refresh_btn.click(
        refresh_history_list,
        None,
        history_dropdown
    )

    demo.load(refresh_history_list, None, history_dropdown)

    # 绑定新按钮和文本框
    gen_voice_btn.click(
        generate_voice_from_text,
        [selected_text],
        [audio_output, status]
    )
    save_voice_btn.click(
        save_voice_from_text,
        [selected_text],
        [audio_output, status]
    )

    # 绑定聊天记录选择事件
    chatbot.select(on_chat_select, [state], selected_text)

# ================== 启动前准备 ==================
_saved_proxy = {}
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    if key in os.environ:
        _saved_proxy[key] = os.environ.pop(key)

def preload_common_audio():
    """预生成常用回复语音，带错误处理"""
    COMMON_RESPONSES = [
        "你好", "嗯……", "是的", "不是呢", "谢谢", "再见",
        "今天天气真好呢", "嗯，我明白了", "有点不太想提", "要尝尝橡木蛋糕卷吗？"
    ]
    logger.info("开始预生成常用语音...")
    for text in COMMON_RESPONSES:
        if text not in _audio_cache:
            try:
                audio_path = text_to_speech(text)
                if audio_path:
                    logger.info(f"预生成成功: {text}")
                else:
                    logger.warning(f"预生成失败: {text}")
            except Exception as e:
                logger.error(f"预生成异常 {text}: {e}")
    logger.info("预生成完成")

preload_common_audio()
demo.launch(share=False, css=custom_css)

for key, value in _saved_proxy.items():
    os.environ[key] = value