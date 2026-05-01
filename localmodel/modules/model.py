"""Qwen2 模型加载与流式推理"""
import os
import sys

# 移除 Anaconda PATH 防止 OpenMP DLL 冲突（兜底）
_path = os.environ.get('PATH', '')
_cleaned = _path.replace('D:\\anaconda3\\Library\\bin;', '') \
                .replace('D:\\anaconda3\\Library\\bin', '')
if _cleaned != _path:
    os.environ['PATH'] = _cleaned
os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')

import time
import torch
from threading import Thread, Lock
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
    TextIteratorStreamer, StoppingCriteria, StoppingCriteriaList,
)
from modules.config import MODEL_PATH, logger

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
    """4-bit 量化加载到 GPU（需要 ~4.5GB 空闲显存）"""
    global _tokenizer, _model, _using_quantization
    _tokenizer = AutoTokenizer.from_pretrained(
        MODEL_PATH, trust_remote_code=True, local_files_only=True,
    )
    quant = BitsAndBytesConfig(load_in_4bit=True)
    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
        device_map='auto',
        quantization_config=quant,
        attn_implementation='sdpa',
        local_files_only=True,
        low_cpu_mem_usage=True,
    )
    _using_quantization = True
    logger.info(f'4-bit 量化加载成功，显存占用 {torch.cuda.memory_allocated()/1024**3:.1f}GB')


def _load_hybrid():
    """bfloat16 CPU 加载 + 将部分层分配到 GPU"""
    global _tokenizer, _model, _using_quantization
    _tokenizer = AutoTokenizer.from_pretrained(
        MODEL_PATH, trust_remote_code=True, local_files_only=True,
    )
    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
        device_map='cpu',
        attn_implementation='sdpa',
        local_files_only=True,
        low_cpu_mem_usage=True,
    )
    _using_quantization = False
    if torch.cuda.is_available() and torch.cuda.mem_get_info()[0] > 2 * 1024**3:
        from accelerate import dispatch_model, infer_auto_device_map
        free_gpu, total_gpu = torch.cuda.mem_get_info()
        try:
            device_map = infer_auto_device_map(
                _model,
                max_memory={0: f'{int(min(free_gpu * 0.9, total_gpu * 0.85)/1024**3)}GiB',
                            'cpu': '14GiB'},
                no_split_module_classes=['Qwen2DecoderLayer'],
            )
            dispatch_model(_model, device_map=device_map)
            gpu_n = sum(1 for v in device_map.values() if v == 0)
            cpu_n = sum(1 for v in device_map.values() if v == 'cpu')
            logger.info(f'模型分配: GPU {gpu_n} 模块 ({torch.cuda.memory_allocated()/1024**3:.1f}GB) + CPU {cpu_n} 模块')
        except Exception as e:
            logger.warning(f'GPU 分配失败，留在 CPU: {e}')


def load_model():
    global _tokenizer, _model, _using_quantization
    if _model is not None:
        return _model, _tokenizer

    with _load_lock:
        if _model is not None:
            return _model, _tokenizer

        logger.info('正在加载模型，请稍候...')
        torch.cuda.empty_cache()

        # 策略 1：4-bit 量化（最快，需要 ~4.5GB 空闲显存）
        if torch.cuda.is_available():
            free_gpu = torch.cuda.mem_get_info()[0]
            total_gpu = torch.cuda.get_device_properties(0).total_memory
            logger.info(f'GPU 空闲显存: {free_gpu/1024**3:.1f}GB / {total_gpu/1024**3:.1f}GB')
            if free_gpu > 4.5 * 1024**3:
                try:
                    _load_4bit_quantized()
                    logger.info(f'加载完成, Attention: {_model.config._attn_implementation}')
                    return _model, _tokenizer
                except Exception as e:
                    logger.warning(f'4-bit 量化失败: {e}，回退中...')
                    _tokenizer = None
                    _model = None
                    torch.cuda.empty_cache()
            else:
                logger.info(f'显存不足需 4.5GB 实际仅 {free_gpu/1024**3:.1f}GB，跳过量化')

        # 策略 2：bfloat16 CPU + 部分 GPU offload
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


def chat_with_liuying_stream(messages: list, **overrides):
    model, tokenizer = load_model()

    start_time = time.time()
    logger.info('开始生成模型回复...')
    try:
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors='pt')
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        generation_kwargs = {
            'input_ids': inputs['input_ids'],
            'attention_mask': inputs['attention_mask'],
            'max_new_tokens': overrides.get('max_new_tokens', 300),
            'temperature': overrides.get('temperature', 0.6),
            'top_p': overrides.get('top_p', 0.9),
            'do_sample': True,
            'repetition_penalty': overrides.get('repetition_penalty', 1.1),
            'pad_token_id': tokenizer.eos_token_id,
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
    except Exception as e:
        logger.error(f'模型生成异常: {e}', exc_info=True)
        yield '抱歉，我遇到了一些问题……可以再试一次吗？'
