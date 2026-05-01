"""Qwen2 模型加载与流式推理"""
import time
import torch
from threading import Thread, Lock
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
    TextIteratorStreamer, StoppingCriteria, StoppingCriteriaList,
)
from modules.config import MODEL_PATH, logger

# 4-bit 量化配置
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type='nf4',
)

# 模块级变量
_tokenizer = None
_model = None
_load_lock = Lock()
_stop_requested = False


class _StopOnFlag(StoppingCriteria):
    """当 _stop_requested 被设置时通知模型停止生成"""
    def __call__(self, input_ids, scores, **kwargs):
        return _stop_requested


def request_stop():
    """请求停止当前生成"""
    global _stop_requested
    _stop_requested = True


def clear_stop_flag():
    """清除停止标记（每次生成前调用）"""
    global _stop_requested
    _stop_requested = False


def is_stop_requested() -> bool:
    """检查是否收到停止请求"""
    return _stop_requested


def load_model():
    """加载模型（线程安全，仅首次调用时执行）"""
    global _tokenizer, _model
    if _model is not None:
        return _model, _tokenizer

    with _load_lock:
        # 二次检查：拿到锁后可能已被其他线程加载
        if _model is not None:
            return _model, _tokenizer

        logger.info('正在加载模型，请稍候...')
        try:
            _tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True, local_files_only=True)
            _model = AutoModelForCausalLM.from_pretrained(
                MODEL_PATH,
                trust_remote_code=True,
                device_map='auto',
                quantization_config=quantization_config,
                attn_implementation='sdpa',
                local_files_only=True,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
            )
            logger.info(f'模型加载完成，Attention 实现: {_model.config._attn_implementation}')
        except Exception as e:
            logger.error(f'模型加载失败: {e}', exc_info=True)
            raise

    return _model, _tokenizer


def is_model_loaded() -> bool:
    """检查模型是否已加载"""
    return _model is not None


def chat_with_liuying_stream(messages: list, **overrides):
    """流式生成回复，返回文本生成器

    overrides 可覆盖默认生成参数：temperature, top_p, max_new_tokens, repetition_penalty
    """
    model, tokenizer = load_model()

    start_time = time.time()
    logger.info('开始生成模型回复...')
    try:
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors='pt').to(model.device)
        generation_kwargs = {
            'input_ids': inputs.input_ids,
            'attention_mask': inputs.attention_mask,
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
