"""历史对话管理（保存、加载、删除、列表、清理）"""
import os
import json
import glob
import time as _time
from datetime import datetime
import gradio as gr
from modules.config import HISTORY_DIR, logger


def get_history_files() -> list[str]:
    """返回所有历史文件（按修改时间倒序）"""
    files = glob.glob(os.path.join(HISTORY_DIR, 'chat_*.json'))
    files.sort(key=os.path.getmtime, reverse=True)
    return files


def get_history_display_name(filepath: str) -> str:
    """生成显示名称：时间 + 对话主题（首条用户消息）"""
    basename = os.path.basename(filepath)
    timestamp = basename.replace('chat_', '').replace('.json', '')
    try:
        dt = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
        time_str = dt.strftime('%m-%d %H:%M')
    except ValueError:
        time_str = timestamp
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            history = json.load(f)
        # 找第一条用户消息作为主题
        first_user = ''
        for msg in history:
            if msg.get('role') == 'user':
                first_user = msg.get('content', '').strip()
                break
        if first_user:
            summary = first_user[:12] + '…' if len(first_user) > 12 else first_user
        else:
            summary = '(空)'
    except Exception:
        summary = '读取失败'
    return f'{time_str} {summary}'


def load_history(selected_file: str, history_state: list):
    """加载选中的历史对话"""
    if not selected_file:
        return history_state, history_state, '请先选择一个历史文件', gr.update()
    try:
        with open(selected_file, 'r', encoding='utf-8') as f:
            loaded_history = json.load(f)
        if isinstance(loaded_history, list):
            logger.info(f'加载历史文件: {selected_file}')
            name = get_history_display_name(selected_file)
            return loaded_history, loaded_history, f'已加载 {name}', gr.update()
        return history_state, history_state, '文件格式错误', gr.update()
    except Exception as e:
        logger.error(f'加载历史失败: {e}', exc_info=True)
        return history_state, history_state, f'加载失败：{e}', gr.update()


def save_history(history: list, status_text: str):
    """保存当前对话到新文件"""
    if not history:
        return '没有对话可保存', status_text, gr.update(choices=[])
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(HISTORY_DIR, f'chat_{timestamp}.json')
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        logger.info(f'保存对话: {filename}')
        files = get_history_files()
        choices = [(get_history_display_name(f), f) for f in files]
        return f'对话已保存为 {get_history_display_name(filename)}', status_text, gr.update(choices=choices)
    except Exception as e:
        logger.error(f'保存失败: {e}', exc_info=True)
        return f'保存失败：{e}', status_text, gr.update(choices=[])


def delete_history(selected_file: str, status_text: str):
    """删除选中的历史文件"""
    if not selected_file:
        return '请先选择要删除的历史记录', status_text, gr.update()
    if not os.path.exists(selected_file):
        return '文件不存在', status_text, gr.update()
    try:
        os.remove(selected_file)
        logger.info(f'删除历史文件: {selected_file}')
        files = get_history_files()
        choices = [(get_history_display_name(f), f) for f in files]
        return f'已删除 {os.path.basename(selected_file)}', status_text, gr.update(choices=choices)
    except Exception as e:
        logger.error(f'删除失败: {e}', exc_info=True)
        return f'删除失败：{e}', status_text, gr.update(choices=[])


def refresh_history_list():
    """刷新下拉菜单选项"""
    files = get_history_files()
    choices = [(get_history_display_name(f), f) for f in files]
    return gr.update(choices=choices)


EXPORT_DIR = os.path.join(os.path.dirname(HISTORY_DIR), 'exports')
os.makedirs(EXPORT_DIR, exist_ok=True)


def export_history(history: list) -> str:
    """将当前对话导出为 Markdown 文件，返回文件路径"""
    if not history:
        return ''
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(EXPORT_DIR, f'对话记录_{timestamp}.md')
    lines = ['# 与流萤的对话记录\n', f'导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n', '---\n']
    for msg in history:
        role = msg.get('role', '')
        content = msg.get('content', '')
        if role == 'user':
            lines.append(f'\n**你：** {content}\n')
        elif role == 'assistant':
            lines.append(f'\n**流萤：** {content}\n')
        elif role == 'system':
            lines.append(f'\n*系统提示：* {content[:50]}…\n')
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        logger.info(f'对话已导出: {filename}')
        return filename
    except Exception as e:
        logger.error(f'导出失败: {e}', exc_info=True)
        return ''


def cleanup_old_histories(max_count: int = 50, max_age_days: int = 90):
    """清理历史文件：保留最近 max_count 条，删除超过 max_age_days 天的"""
    files = get_history_files()
    deleted = 0
    # 清理超出数量限制的旧文件
    for f in files[max_count:]:
        try:
            # 同时检查年龄
            age_days = (_time.time() - os.path.getmtime(f)) / 86400
            if age_days > max_age_days:
                os.remove(f)
                deleted += 1
        except OSError:
            pass
    if deleted:
        logger.info(f'已清理 {deleted} 个过期历史文件')
