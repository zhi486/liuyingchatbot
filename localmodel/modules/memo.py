"""备忘录管理：自然语言时间解析 + CRUD + 意图匹配"""
import os
import json
import re
import uuid
from datetime import datetime, timedelta
from modules.config import BASE_DIR, logger

MEMO_DIR = os.path.join(BASE_DIR, 'memos')
os.makedirs(MEMO_DIR, exist_ok=True)
MEMO_FILE = os.path.join(MEMO_DIR, 'memos.json')

# ── 星期映射 ──
_WEEKDAY_MAP = {
    '周一': 0, '周二': 1, '周三': 2, '周四': 3, '周五': 4, '周六': 5, '周日': 6,
    '星期一': 0, '星期二': 1, '星期三': 2, '星期四': 3, '星期五': 4, '星期六': 5, '星期日': 6,
    '礼拜一': 0, '礼拜二': 1, '礼拜三': 2, '礼拜四': 3, '礼拜五': 4, '礼拜六': 5, '礼拜天': 6,
    '周天': 6,
}


def _load_memos() -> list[dict]:
    if not os.path.exists(MEMO_FILE):
        return []
    try:
        with open(MEMO_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_memos(memos: list[dict]):
    with open(MEMO_FILE, 'w', encoding='utf-8') as f:
        json.dump(memos, f, ensure_ascii=False, indent=2)


def _parse_cn_datetime(text: str) -> datetime | None:
    """从中文自然语言中解析日期时间，返回 datetime 或 None"""
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    result_date = None
    result_hour = None
    result_minute = 0

    # ── 日期解析 ──
    if m := re.search(r'(\d{1,2})月(\d{1,2})[日号]', text):
        month, day = int(m.group(1)), int(m.group(2))
        result_date = today.replace(month=month, day=day)
        if result_date < today:
            result_date = result_date.replace(year=result_date.year + 1)
    elif '今天' in text or '今晚' in text or '今早' in text or '今晨' in text:
        result_date = today
    elif '明天' in text or '明晚' in text or '明早' in text:
        result_date = today + timedelta(days=1)
    elif '后天' in text:
        result_date = today + timedelta(days=2)
    elif '大后天' in text:
        result_date = today + timedelta(days=3)
    elif '下周' in text:
        for name, wd in _WEEKDAY_MAP.items():
            if name in text:
                days_ahead = (7 + wd - today.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                result_date = today + timedelta(days=days_ahead + 7)
                break
    else:
        for name, wd in _WEEKDAY_MAP.items():
            if name in text:
                days_ahead = (7 + wd - today.weekday()) % 7
                result_date = today + timedelta(days=days_ahead)
                break

    # ── 时间解析 ──
    time_match = re.search(
        r'(上午|中午|下午|傍晚|晚上|早上|早晨|凌晨)?\s*(\d{1,2})[点时:](\d{1,2})?\s*[分]?',
        text
    )
    period_map = {
        '凌晨': 0, '早上': 7, '早晨': 7, '上午': 0, '中午': 12,
        '下午': 12, '傍晚': 17, '晚上': 19,
    }
    if time_match:
        period = time_match.group(1) or ''
        h = int(time_match.group(2))
        m = int(time_match.group(3)) if time_match.group(3) else 0

        if period in period_map:
            base = period_map[period]
            if h == 12:
                h = 0
            if period in ('下午', '傍晚', '晚上') and h < 12:
                h += 12
            if h < base:
                h += 12
        result_hour = h
        result_minute = m
    elif m := re.search(r'(上午|中午|下午|傍晚|晚上|早上|早晨|凌晨)(\d{1,2})[点时]', text):
        period = m.group(1)
        h = int(m.group(2))
        base = period_map.get(period, 0)
        if period in ('下午', '傍晚', '晚上'):
            if h != 12:
                h += 12
        elif period in ('凌晨',) and h == 12:
            h = 0
        elif period == '上午' and h == 12:
            h = 0
        result_hour = h
        result_minute = 0

    # 修正：没有时段前缀但文本暗示晚上/傍晚（如"今晚8点"）
    if result_hour is not None and result_hour <= 11:
        if re.search(r'(今|明|后)晚', text) or '傍晚' in text:
            result_hour += 12

    if result_date is None:
        return None
    if result_hour is not None:
        return result_date.replace(hour=result_hour, minute=result_minute, second=0, microsecond=0)
    return result_date


def _extract_content(text: str) -> str:
    """从消息中提取备忘录内容（去除触发词和时间信息）"""
    content = text
    # 去掉触发词
    for kw in ['提醒我', '记住', '记录一下', '记一下', '备忘录添加', '安排一下', '别忘了',
               '帮我记一下', '帮我记住', '添加备忘录', '新增备忘录', '设置提醒']:
        content = content.replace(kw, '', 1)
    # 去掉时间表达式
    content = re.sub(r'\d{1,2}月\d{1,2}[日号]', '', content)
    content = re.sub(r'(今天|明天|后天|大后天|今晚|明晚|后晚|今早|明早|下周[一二三四五六日天]|周[一二三四五六日天])', '', content)
    content = re.sub(r'(上午|中午|下午|傍晚|晚上|早上|早晨|凌晨)\s*\d{1,2}[点时:]\d{0,2}\s*[分]?', '', content)
    content = re.sub(r'(今|明|后)(晚|早|晨)\s*\d{1,2}[点时:]\d{0,2}\s*[分]?', '', content)
    content = re.sub(r'\d{1,2}[点时:]\d{0,2}\s*[分]?', '', content)
    content = re.sub(r'[，,。\.\s]+', ' ', content).strip()
    return content or '未命名备忘录'


# ── 意图匹配正则 ──
MEMO_ADD_PATTERN = re.compile(
    r'(提醒我|记住|记录一下|记一下|安排一下|别忘了|帮我记|帮我记住|设置提醒|添加备忘录|新增备忘录)',
    re.IGNORECASE,
)

MEMO_LIST_PATTERN = re.compile(
    r'(查看备忘录|我的备忘录|我的安排|有什么提醒|查看提醒|备忘录列表|我的日程|查看日程|'
    r'今天有什么(安排|提醒|日程|备忘录)|明天有什么(安排|提醒|日程|备忘录)|'
    r'这周有什么(安排|提醒|日程|备忘录)|下周有什么(安排|提醒|日程|备忘录)|'
    r'最近有什么(安排|提醒|日程|备忘录))',
    re.IGNORECASE,
)

_CN_NUM = r'[一二三四五六七八九十]+'

MEMO_DONE_PATTERN = re.compile(
    r'(完成|做完|搞定|标记完成)\s*(第?\s*(?:\d+|' + _CN_NUM + r')|全部)?\s*(个|条|项)?\s*(提醒|备忘录|日程|安排)',
    re.IGNORECASE,
)

MEMO_DELETE_PATTERN = re.compile(
    r'(删除|取消|去掉|移除|删掉)\s*(第?\s*(?:\d+|' + _CN_NUM + r')|全部)?\s*(个|条|项)?\s*(提醒|备忘录|日程|安排)',
    re.IGNORECASE,
)

MEMO_MODIFY_PATTERN = re.compile(
    r'(修改|更改|改一下|更新|改成|改为|调整一下|调整|变更|换一下|换成|改到|改一下时间|改一下内容|'
    r'更新一下)\s*(第?\s*(?:\d+|' + _CN_NUM + r')|全部)?\s*(个|条|项)?',
    re.IGNORECASE,
)

MEMO_GUIDE_PATTERN = re.compile(
    r'(备忘录|待办事项|待办列表|提醒事项|日程管理|todo\s*list|我的日程|我的安排|'
    r'帮我管理|怎么用备忘录|教我.*备忘录)',
    re.IGNORECASE,
)


# ── 核心操作 ──

def add_memo(content: str, dt: datetime | None) -> str:
    """添加一条备忘录，返回流萤风格的回复文本"""
    memos = _load_memos()
    entry = {
        'id': uuid.uuid4().hex[:8],
        'content': content,
        'datetime': dt.isoformat() if dt else None,
        'created_at': datetime.now().isoformat(),
        'status': 'pending',
    }
    memos.append(entry)
    _save_memos(memos)
    logger.info(f'添加备忘录: {content} @ {dt}')

    if dt:
        time_str = dt.strftime('%m月%d日 %H:%M') if dt.hour or dt.minute else dt.strftime('%m月%d日')
        return f'嗯，我记下了～「{content}」会在 **{time_str}** 提醒你呢。'
    else:
        return f'好的，已经帮你记下来了～「{content}」'


def list_memos(filter_text: str = '') -> str:
    """列出备忘录，返回流萤风格的回复"""
    memos = _load_memos()
    pending = [m for m in memos if m['status'] == 'pending']

    # 过滤：今天
    if any(kw in filter_text for kw in ('今天', '今日')):
        today_str = datetime.now().strftime('%Y-%m-%d')
        pending = [m for m in pending if m['datetime'] and m['datetime'][:10] == today_str]
    # 过滤：明天
    elif '明天' in filter_text:
        tomorrow_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        pending = [m for m in pending if m['datetime'] and m['datetime'][:10] == tomorrow_str]

    pending.sort(key=lambda m: m['datetime'] or '9999')

    if not pending:
        if '今天' in filter_text:
            return '今天没有特别的安排呢……可以好好放松一下～'
        elif '明天' in filter_text:
            return '明天暂时还没有安排呢。'
        return '目前没有待办的提醒哦，有什么需要我帮你记住的吗？'

    lines = ['这是你当前的待办事项：\n']
    for i, m in enumerate(pending, 1):
        content = m['content']
        if m['datetime']:
            try:
                dt = datetime.fromisoformat(m['datetime'])
                if dt.hour or dt.minute:
                    time_str = dt.strftime('%m月%d日 %H:%M')
                else:
                    time_str = dt.strftime('%m月%d日')
            except ValueError:
                time_str = m['datetime']
            lines.append(f'{i}. 📅 {time_str} — {content}')
        else:
            lines.append(f'{i}. 📝 {content}')
    return '\n'.join(lines)


def complete_memo(text: str) -> str:
    """完成备忘录"""
    memos = _load_memos()
    pending = [m for m in memos if m['status'] == 'pending']

    # 全部完成
    if '全部' in text:
        for m in pending:
            m['status'] = 'done'
        _save_memos(memos)
        return f'嗯，{len(pending)} 条提醒都标记为完成啦。'

    # 按序号完成
    idx = _extract_index(text)
    if idx is None or idx < 1 or idx > len(pending):
        return '嗯……我没找到对应序号的提醒呢。你可以说"完成第一条提醒"试试～'
    m = pending[idx - 1]
    m['status'] = 'done'
    _save_memos(memos)
    return f'好～「{m["content"]}」已经完成啦。'


def delete_memo(text: str) -> str:
    """删除备忘录"""
    memos = _load_memos()
    pending = [(i, m) for i, m in enumerate(memos) if m['status'] == 'pending']

    # 全部删除
    if '全部' in text:
        for _, m in pending:
            m['status'] = 'cancelled'
        _save_memos(memos)
        return f'嗯，{len(pending)} 条提醒都已取消。'

    # 按序号删除
    idx = _extract_index(text)
    if idx is None or idx < 1 or idx > len(pending):
        return '嗯……我没找到对应序号的提醒呢。你可以说"删除第一条提醒"试试～'

    m = pending[idx - 1][1]
    m['status'] = 'cancelled'
    _save_memos(memos)
    return f'好的，「{m["content"]}」已经取消啦。'


def modify_memo(text: str) -> str:
    """修改备忘录的内容或时间"""
    memos = _load_memos()
    pending = [(i, m) for i, m in enumerate(memos) if m['status'] == 'pending']

    idx = _extract_index(text)
    if idx is None:
        return '嗯……你想修改哪一条呢？可以说"修改第一条"或"把第二条改成明天"哦～'
    if idx < 1 or idx > len(pending):
        return f'目前只有 {len(pending)} 条待办呢，序号超出啦……'

    target = pending[idx - 1][1]

    # 解析新的日期时间
    new_dt = _parse_cn_datetime(text)

    # 解析新的内容（"改成/改为"之后的部分）
    new_content = None
    content_match = re.search(r'(?:改成|改为|换成|修改成|改成内容|修改为)\s*(.+?)(?:\s*[，,。\.]|$)', text)
    if content_match:
        raw = content_match.group(1).strip()
        # 去除残留的时间表达式
        raw = re.sub(r'\d{1,2}月\d{1,2}[日号]', '', raw)
        raw = re.sub(r'(今天|明天|后天|大后天|今晚|明晚|后晚|今早|明早|下周[一二三四五六日天]|周[一二三四五六日天])', '', raw)
        raw = re.sub(r'(上午|中午|下午|傍晚|晚上|早上|早晨|凌晨)\s*\d{1,2}[点时:]\d{0,2}\s*[分]?', '', raw)
        raw = re.sub(r'\d{1,2}[点时:]\d{0,2}\s*[分]?', '', raw)
        raw = re.sub(r'[，,。\.\s]+', ' ', raw).strip()
        if raw:
            new_content = raw

    if new_dt and new_content:
        target['datetime'] = new_dt.isoformat()
        target['content'] = new_content
        _save_memos(memos)
        time_str = new_dt.strftime('%m月%d日 %H:%M') if (new_dt.hour or new_dt.minute) else new_dt.strftime('%m月%d日')
        return f'好的，已经帮你把这条改成「{new_content}」，时间更新为 {time_str} 啦～'
    elif new_dt:
        target['datetime'] = new_dt.isoformat()
        _save_memos(memos)
        time_str = new_dt.strftime('%m月%d日 %H:%M') if (new_dt.hour or new_dt.minute) else new_dt.strftime('%m月%d日')
        return f'嗯，时间已经更新为 {time_str} 了～「{target["content"]}」'
    elif new_content:
        target['content'] = new_content
        _save_memos(memos)
        return f'好的，内容已更新为「{new_content}」～'
    else:
        return f'嗯……你想把这条改成什么呢？可以说"修改第一条，改成明天下午3点"或"把第二条改成买水果"哦～'


def guide_memo(text: str) -> str:
    """当用户泛泛提到「备忘录」时，主动引导操作"""
    memos = _load_memos()
    pending = [m for m in memos if m['status'] == 'pending']

    # 以下引导词表示用户想添加，避免误拦截
    if MEMO_ADD_PATTERN.search(text):
        return None  # 走到 add 逻辑

    if pending:
        lines = ['嗯，这是你当前的待办事项，我可以帮你管理它们：\n']
        for i, m in enumerate(pending, 1):
            content = m['content']
            if m['datetime']:
                try:
                    dt = datetime.fromisoformat(m['datetime'])
                    time_str = dt.strftime('%m月%d日 %H:%M') if (dt.hour or dt.minute) else dt.strftime('%m月%d日')
                except ValueError:
                    time_str = m['datetime']
                lines.append(f'{i}. 📅 {time_str} — {content}')
            else:
                lines.append(f'{i}. 📝 {content}')
        lines.append('\n你可以对我说：\n'
                     '📝 「添加备忘录」— 新建提醒\n'
                     '✏️ 「修改第一条」— 修改内容或时间\n'
                     '✅ 「完成第一条」— 标记完成\n'
                     '🗑️ 「删除第二条」— 取消提醒\n'
                     '📋 「查看备忘录」— 查看列表')
        return '\n'.join(lines)
    else:
        return ('目前没有待办事项呢……需要我帮你记一个吗？\n\n'
                '比如你可以说：\n'
                '📝 「提醒我明天下午3点开会」\n'
                '📝 「记录一下周五买水果」\n'
                '📝 「安排一下下周一提交报告」')


def _extract_index(text: str) -> int | None:
    """提取中文数字索引，兼容「第一个」「第2条」等带量词模式"""
    cn_num = {
        '第一': 1, '第二': 2, '第三': 3, '第四': 4, '第五': 5,
        '第六': 6, '第七': 7, '第八': 8, '第九': 9, '第十': 10,
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    }
    # 「第N个/条/项」模式优先
    if m := re.search(r'第\s*(\d+)\s*[个条项]?', text):
        return int(m.group(1))
    for word, num in cn_num.items():
        if word in text:
            return num
    if m := re.search(r'(?:^|[^\d])(\d+)\s*[个条项]?', text):
        return int(m.group(1))
    return None


# ── UI 导向函数 ──

def get_memos_for_ui(status_filter: str = "all") -> list[dict]:
    """返回结构化备忘录数据供前端使用"""
    memos = _load_memos()
    if status_filter != "all":
        memos = [m for m in memos if m['status'] == status_filter]
    memos.sort(key=lambda m: m['datetime'] or '9999')
    return memos


def add_memo_ui(content: str, date_str: str, time_str: str, priority: str) -> tuple[str, str]:
    """从 UI 表单添加备忘录，返回 (html, status_msg)"""
    content = content.strip()
    if not content:
        return render_memo_cards("pending"), "内容不能为空"

    dt = None
    if date_str:
        try:
            from datetime import datetime as dt_cls
            parts = date_str.strip().split('-')
            if len(parts) == 3:
                hour, minute = 0, 0
                if time_str and ':' in time_str:
                    hour, minute = map(int, time_str.strip().split(':'))
                dt = dt_cls(int(parts[0]), int(parts[1]), int(parts[2]), hour, minute)
            else:
                return render_memo_cards("pending"), "日期格式应为 YYYY-MM-DD"
        except (ValueError, IndexError):
            return render_memo_cards("pending"), "日期格式错误，请使用 YYYY-MM-DD"

    memos = _load_memos()
    entry = {
        'id': uuid.uuid4().hex[:8],
        'content': content,
        'datetime': dt.isoformat() if dt else None,
        'created_at': datetime.now().isoformat(),
        'status': 'pending',
        'priority': priority or 'medium',
    }
    memos.append(entry)
    _save_memos(memos)
    logger.info(f'[UI] 添加备忘录: {content} @ {dt} [{priority}]')
    return render_memo_cards("pending"), f'已添加「{content}」'


def toggle_memo_ui(memo_id: str) -> tuple[str, str]:
    """切换备忘录完成状态，返回 (html, status_msg)"""
    memos = _load_memos()
    for m in memos:
        if m['id'] == memo_id:
            if m['status'] == 'pending':
                m['status'] = 'done'
                msg = f'「{m["content"]}」已完成'
            elif m['status'] == 'done':
                m['status'] = 'pending'
                msg = f'「{m["content"]}」已恢复为待办'
            else:
                return render_memo_cards("pending"), '该备忘录已取消，无法操作'
            _save_memos(memos)
            logger.info(f'[UI] 切换备忘录状态: {memo_id} -> {m["status"]}')
            return render_memo_cards("pending"), msg
    return render_memo_cards("pending"), '未找到该备忘录'


def delete_memo_ui(memo_id: str) -> tuple[str, str]:
    """软删除备忘录，返回 (html, status_msg)"""
    memos = _load_memos()
    for m in memos:
        if m['id'] == memo_id:
            m['status'] = 'cancelled'
            _save_memos(memos)
            logger.info(f'[UI] 删除备忘录: {memo_id}')
            return render_memo_cards("pending"), f'已删除「{m["content"]}」'
    return render_memo_cards("pending"), '未找到该备忘录'


def _format_memo_date(datetime_str: str | None) -> str:
    if not datetime_str:
        return ''
    try:
        dt = datetime.fromisoformat(datetime_str)
        if dt.hour or dt.minute:
            return dt.strftime('%m月%d日 %H:%M')
        return dt.strftime('%m月%d日')
    except ValueError:
        return datetime_str


_PRIORITY_COLORS = {'high': '#ef4444', 'medium': '#f59e0b', 'low': '#3b82f6'}
_PRIORITY_LABELS = {'high': '高', 'medium': '中', 'low': '低'}
_STATUS_LABELS = {'pending': ('待办', 'pending'), 'done': ('已完成', 'done'),
                  'cancelled': ('已取消', 'cancelled')}


def render_memo_cards(status_filter: str = "pending") -> str:
    """生成备忘录卡片 HTML（仅展示，操作通过 Gradio 组件）"""
    memos = get_memos_for_ui(status_filter)
    if not memos:
        empty_msgs = {
            'pending': '<div class="memo-empty">🎉 没有待办的备忘录</div>',
            'done': '<div class="memo-empty">📭 还没有已完成的备忘录</div>',
            'all': '<div class="memo-empty">📝 还没有任何备忘录，添加一个吧</div>',
        }
        return empty_msgs.get(status_filter, empty_msgs['all'])

    cards = []
    for m in memos:
        pid = m.get('priority', 'medium')
        pcolor = _PRIORITY_COLORS.get(pid, '#f59e0b')
        plabel = _PRIORITY_LABELS.get(pid, '中')
        slabel, sclass = _STATUS_LABELS.get(m['status'], ('未知', ''))
        dt_str = _format_memo_date(m['datetime'])

        date_html = f'<span class="memo-date">📅 {dt_str}</span>' if dt_str else ''
        cards.append(f'''<div class="memo-card {sclass}">
            <div class="memo-priority" style="background:{pcolor}" title="优先级：{plabel}"></div>
            <div class="memo-body">
                <div class="memo-content">{m['content']}</div>
                <div class="memo-meta">
                    {date_html}
                    <span class="memo-pill">{plabel}优先级</span>
                    <span class="memo-badge {sclass}">{slabel}</span>
                </div>
            </div>
        </div>''')

    return f'<div class="memo-grid">{"".join(cards)}</div>'


def build_memo_choices(status_filter: str = "all") -> list[str]:
    """构建操作下拉列表：序号 + 内容"""
    memos = get_memos_for_ui(status_filter)
    choices = []
    for m in memos:
        pid = m.get('priority', 'medium')
        plabel = _PRIORITY_LABELS.get(pid, '中')
        dt_str = _format_memo_date(m['datetime'])
        suffix = f' [{dt_str}]' if dt_str else ''
        choices.append(f"{m['id']} | {m['content']}{suffix} [{plabel}]")
    return choices


def memo_action(action: str, selected: str, status_filter: str) -> tuple[str, str, list[str]]:
    """Gradio 事件回调：对选中的备忘录执行操作"""
    if not selected:
        return render_memo_cards(status_filter), '请先选择一个备忘录', build_memo_choices(status_filter)

    memo_id = selected.split(' | ')[0].strip()
    if action == 'toggle':
        html, msg = toggle_memo_ui(memo_id)
    elif action == 'delete':
        html, msg = delete_memo_ui(memo_id)
    else:
        html, msg = render_memo_cards(status_filter), '未知操作'

    return html, msg, build_memo_choices(status_filter)


def handle_memo_intent(message: str) -> str | None:
    """检测消息中的备忘录意图，命中则返回回复文本，否则返回 None"""
    text = message.strip()

    # 1. 列出备忘录
    if MEMO_LIST_PATTERN.search(text):
        return list_memos(text)

    # 2. 完成备忘录
    if MEMO_DONE_PATTERN.search(text):
        return complete_memo(text)

    # 3. 删除备忘录
    if MEMO_DELETE_PATTERN.search(text):
        return delete_memo(text)

    # 4. 修改备忘录
    if MEMO_MODIFY_PATTERN.search(text):
        return modify_memo(text)

    # 5. 添加备忘录
    if MEMO_ADD_PATTERN.search(text):
        dt = _parse_cn_datetime(text)
        content = _extract_content(text)
        return add_memo(content, dt)

    # 6. 备忘录引导（兜底，最低优先级）
    if MEMO_GUIDE_PATTERN.search(text):
        return guide_memo(text)

    return None
