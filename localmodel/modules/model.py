"""Qwen2 模型加载与流式推理"""
import os
import sys

# 移除 Anaconda PATH 防止 OpenMP DLL 冲突（兜底）
_path = os.environ.get('PATH', '')
_entries = _path.split(';')
_cleaned_entries = [e for e in _entries if 'anaconda' not in e.lower()]
if len(_cleaned_entries) != len(_entries):
    os.environ['PATH'] = ';'.join(_cleaned_entries)
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import time
import torch
from threading import Thread, Lock
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
    TextIteratorStreamer, StoppingCriteria, StoppingCriteriaList,
)
from modules.config import MODEL_PATH, logger

# flash-attn 可选安装，检测后决定 attention 实现
try:
    import flash_attn  # noqa: F401
    _HAS_FLASH_ATTN = True
except ImportError:
    _HAS_FLASH_ATTN = False

_tokenizer = None
_model = None
_load_lock = Lock()
_stop_requested = False
_using_quantization = False


class _StopOnFlag(StoppingCriteria):
    def __call__(self, input_ids, scores, **kwargs):
        return _stop_requested


def request_stop():
    global _stop_requested
    _stop_requested = True


def clear_stop_flag():
    global _stop_requested
    _stop_requested = False


def is_stop_requested():
    return _stop_requested


def _load_4bit_quantized():
    """4-bit 量化 — 全部尽可能放到 GPU"""
    global _tokenizer, _model, _using_quantization
    _tokenizer = AutoTokenizer.from_pretrained(
        MODEL_PATH, trust_remote_code=True, local_files_only=True,
    )
    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type='nf4',
    )
    attn = 'flash_attention_2' if (_HAS_FLASH_ATTN and torch.cuda.is_available()) else 'sdpa'
    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
        device_map='auto',
        quantization_config=quant,
        attn_implementation=attn,
        local_files_only=True,
    )
    _using_quantization = True
    logger.info(f'4-bit 量化加载成功，显存占用 {torch.cuda.memory_allocated()/1024**3:.1f}GB，Attention: {attn}')


def _load_hybrid():
    """GPU 为主 + CPU 为辅：自动分配层，优先使用 GPU 显存"""
    global _tokenizer, _model, _using_quantization
    _tokenizer = AutoTokenizer.from_pretrained(
        MODEL_PATH, trust_remote_code=True, local_files_only=True,
    )

    free_gpu, total_gpu = 0, 0
    if torch.cuda.is_available():
        free_gpu, total_gpu = torch.cuda.mem_get_info()

    # 自动选择 attention 实现：flash_attention_2 最快（需安装 flash-attn）
    attn = 'flash_attention_2' if (_HAS_FLASH_ATTN and torch.cuda.is_available()) else 'sdpa'

    # 用 max_memory 引导：GPU 放得下多少就放多少，超额部分自动溢出到 CPU
    max_memory = None
    if torch.cuda.is_available() and free_gpu > 1 * 1024**3:
        gpu_limit = int(min(free_gpu * 0.9, total_gpu * 0.85) / 1024**3)
        max_memory = {0: f'{max(gpu_limit, 1)}GiB', 'cpu': '32GiB'}

    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
        device_map='auto' if max_memory else 'cpu',
        max_memory=max_memory,
        attn_implementation=attn,
        local_files_only=True,
    )
    _using_quantization = False

    if _model.device.type == 'cuda':
        logger.info(f'模型在 GPU 上运行，显存占用 {torch.cuda.memory_allocated()/1024**3:.1f}GB')
    else:
        gpu_layers = sum(1 for p in _model.parameters() if p.device.type == 'cuda')
        total_layers = sum(1 for _ in _model.parameters())
        logger.info(f'模型分布在 CPU+GPU，GPU 层: {gpu_layers}/{total_layers}')


def load_model():
    global _tokenizer, _model, _using_quantization
    if _model is not None:
        return _model, _tokenizer

    with _load_lock:
        if _model is not None:
            return _model, _tokenizer

        logger.info('正在加载模型，请稍候...')
        torch.cuda.empty_cache()

        # 策略 1：4-bit 量化（优先 GPU，自动 CPU offload）
        if torch.cuda.is_available():
            free_gpu = torch.cuda.mem_get_info()[0]
            total_gpu = torch.cuda.get_device_properties(0).total_memory
            logger.info(f'GPU 空闲显存: {free_gpu/1024**3:.1f}GB / {total_gpu/1024**3:.1f}GB')
            try:
                _load_4bit_quantized()
                logger.info(f'加载完成, Attention: {_model.config._attn_implementation}')
                return _model, _tokenizer
            except Exception as e:
                logger.warning(f'4-bit 加载失败: {e}，回退到 bfloat16 混合模式...')
                _tokenizer = None
                _model = None
                torch.cuda.empty_cache()

        # 策略 2：bfloat16 — GPU 为主 + CPU 为辅
        try:
            _load_hybrid()
            logger.info(f'加载完成, Attention: {_model.config._attn_implementation}')
        except OSError as e:
            logger.error(
                '内存不足，无法加载模型。请尝试：'
                '1. 关闭 Edge/Chrome 浏览器和其他程序\n'
                '2. 关闭 Wallpaper Engine 等后台程序\n'
                '3. 重启电脑后直接运行\n'
                f'错误: {e}'
            )
            raise
        except Exception as e:
            logger.error(f'模型加载失败: {e}', exc_info=True)
            raise

    return _model, _tokenizer


def is_model_loaded():
    return _model is not None


# 保留的最大历史轮数（超过则截断最早的，保留最近 N 轮）
_MAX_HISTORY_TURNS = 8


def _truncate_history(messages: list) -> list:
    """截断对话历史，只保留最近 _MAX_HISTORY_TURNS 轮 + system prompt"""
    system_idx = None
    for i, m in enumerate(messages):
        if m.get('role') == 'system':
            system_idx = i
            break
    conversation = messages[system_idx + 1:] if system_idx is not None else messages
    if len(conversation) <= _MAX_HISTORY_TURNS * 2:
        return messages
    # 保留 system + 最近 N 轮
    kept = conversation[-(_MAX_HISTORY_TURNS * 2):]
    if system_idx is not None:
        kept = [messages[system_idx]] + kept
    logger.info(f'历史截断: {len(messages)} 条 -> {len(kept)} 条（保留最近 {_MAX_HISTORY_TURNS} 轮）')
    return kept


def chat_with_liuying_stream(messages: list, **overrides):
    model, tokenizer = load_model()

    start_time = time.time()
    # 截断历史，防止 prompt 过长拖慢推理
    messages = _truncate_history(messages)
    logger.info('开始生成模型回复...')
    try:
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors='pt')
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        max_new_tokens = overrides.get('max_new_tokens', 128)
        generation_kwargs = {
            'input_ids': inputs['input_ids'],
            'attention_mask': inputs['attention_mask'],
            'max_new_tokens': max_new_tokens,
            'temperature': overrides.get('temperature', 0.6),
            'top_p': overrides.get('top_p', 0.9),
            'do_sample': True,
            'repetition_penalty': overrides.get('repetition_penalty', 1.1),
            'pad_token_id': tokenizer.eos_token_id,
            'use_cache': True,
            'stopping_criteria': StoppingCriteriaList([_StopOnFlag()]),
        }
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
        generation_kwargs['streamer'] = streamer
        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()
        full_text = ''
        for text in streamer:
            full_text += text
            yield text
        elapsed = time.time() - start_time
        logger.info(f'模型生成完成，耗时 {elapsed:.2f} 秒，回复长度 {len(full_text)} 字符')
        if max_new_tokens <= 128 and len(full_text) >= max_new_tokens * 0.9:
            logger.warning(f'回复可能被截断（{len(full_text)} 字符接近上限 {max_new_tokens}），建议增大"最大生成长度"滑块')
    except Exception as e:
        logger.error(f'模型生成异常: {e}', exc_info=True)
        yield '抱歉，我遇到了一些问题……可以再试一次吗？'
