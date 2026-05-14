"""流萤聊天机器人 — 主入口"""
import os
import sys

# === 环境修正（必须在任何库导入前执行）===

# 1. 移除所有 Anaconda 的 PATH 条目，防止 libiomp5md.dll 冲突。
#    从 PATH 中用 ; 分割条目，移除所有包含 "anaconda" 的路径。
#    比单一 replace 更可靠，不会因路径格式差异而失效。
_path = os.environ.get('PATH', '')
_entries = _path.split(';')
_cleaned_entries = [e for e in _entries if 'anaconda' not in e.lower()]
if len(_cleaned_entries) != len(_entries):
    os.environ['PATH'] = ';'.join(_cleaned_entries)

# 2. 允许重复 OpenMP 加载（兜底）
os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')

import time
from threading import Thread

import gradio as gr

from modules import (
    logger, avatar_img, restore_proxy, validate_config,
    chat_with_liuying_stream, load_model, request_stop, clear_stop_flag, is_stop_requested,
    voice_to_text,
    text_to_speech, save_voice, preload_common_audio, cleanup_old_voices,
    get_weather_by_city, WEATHER_PATTERN,
    load_history, save_history, delete_history, refresh_history_list, export_history,
    cleanup_old_histories,
    custom_css,
    handle_memo_intent, add_memo_ui, render_memo_cards,
    build_memo_choices, memo_action,
)


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
- 语气：柔和、轻声，偶尔用"……"、"呢"、"吧"表示停顿或犹豫。
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
- 表达情感要含蓄，用行动或细节暗示，不要直白说"我喜欢你"。
- 尽量用短句，保持少女的羞涩感。
- 对失熵症不要详细解释，简单带过即可，重点放在珍惜当下。"""


# ================== 对话处理 ==================
def respond(message, history, temperature, top_p, max_new_tokens, status_text):
    """处理用户消息，支持停止生成"""
    if not message:
        yield history, history, status_text
        return

    clear_stop_flag()
    start_time = time.time()
    logger.info(f"收到用户消息: {message[:50]}...")

    # 备忘录意图优先（自然语言 CRUD，不依赖模型）
    memo_reply = handle_memo_intent(message)
    if memo_reply is not None:
        new_history = history + [{"role": "user", "content": message},
                                 {"role": "assistant", "content": memo_reply}]
        yield new_history, new_history, "备忘录操作完成"  # CSS class handled by Gradio
        return

    # 天气查询优先（不需要模型）
    match = WEATHER_PATTERN.search(message)
    if match:
        city = match.group(1).strip()
        logger.info(f"识别为天气查询，城市: {city}")
        try:
            yield history, history, "正在查询天气..."
            weather_reply = get_weather_by_city(city) if city else "嗯……你想问哪里的天气呢？"
            new_history = history + [{"role": "user", "content": message},
                                     {"role": "assistant", "content": weather_reply}]
            yield new_history, new_history, "天气查询完成"
        except Exception as e:
            logger.error(f"天气查询异常: {e}", exc_info=True)
            error_reply = "抱歉，天气查询出错了……"
            new_history = history + [{"role": "user", "content": message},
                                     {"role": "assistant", "content": error_reply}]
            yield new_history, new_history, "天气查询失败"
        return

    # 正常对话
    temp_history = history + [{"role": "user", "content": message}]
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": message}]
    full_reply = ""
    stopped = False

    try:
        gen_params = {"temperature": temperature, "top_p": top_p, "max_new_tokens": max_new_tokens}
        for chunk in chat_with_liuying_stream(api_messages, **gen_params):
            full_reply += chunk
            current_history = temp_history + [{"role": "assistant", "content": full_reply}]
            yield current_history, current_history, "正在生成..."
            if is_stop_requested():
                stopped = True
                break

        if stopped:
            partial = temp_history + [{"role": "assistant", "content": full_reply + "…"}]
            yield partial, partial, "⏹️ 已停止"
        else:
            final_history = temp_history + [{"role": "assistant", "content": full_reply}]
            elapsed = time.time() - start_time
            logger.info(f"完整对话处理完成，耗时 {elapsed:.2f} 秒")
            yield final_history, final_history, f"就绪（{elapsed:.1f}秒）"
    except Exception as e:
        logger.error(f"对话生成异常: {e}", exc_info=True)
        error_reply = "抱歉，我好像遇到点问题……能再说一次吗？"
        error_history = temp_history + [{"role": "assistant", "content": error_reply}]
        yield error_history, error_history, "❌ 生成失败"
    finally:
        clear_stop_flag()


# ================== 语音处理 ==================
def generate_voice_from_text(text):
    """生成语音"""
    if not text:
        yield None, "没有要生成语音的内容"
        return
    yield None, "语音生成速度受网络波动和句子长短的影响，请耐心等待..."
    audio_path = text_to_speech(text)
    yield (audio_path, "✅ 语音生成完成") if audio_path else (None, "❌ 语音生成失败，请稍后重试")


def save_voice_from_text(text):
    """保存语音"""
    if not text:
        yield None, "没有要保存的内容"
        return
    yield None, "语音生成速度受网络波动和句子长短的影响，请耐心等待..."
    saved_path = save_voice(text)
    yield (saved_path, f"✅ 语音已保存至 {saved_path}") if saved_path else (None, "❌ 保存失败，请检查网络或稍后重试")


def on_chat_select(evt: gr.SelectData, history):
    """点击助手消息时填充到文本框"""
    if evt.index is not None and evt.index < len(history):
        msg = history[evt.index]
        if msg.get("role") == "assistant":
            return msg.get("content", "")
    return ""


def set_voice_text(audio_file, history_state):
    """语音识别结果填入文本框"""
    if audio_file is None:
        return "", history_state
    return voice_to_text(audio_file), history_state


def clear():
    logger.info("清空对话")
    welcome = [{"role": "assistant", "content": "🦋 嗨，我是流萤……今天天气真好呢。想聊聊天吗？或者用语音跟我说说话吧。"}]
    return [], welcome, "对话已清空"


# ================== 备忘录 UI 辅助 ==================
def _refresh_memo_ui(status_filter_val):
    """刷新备忘录面板"""
    return (
        render_memo_cards(status_filter_val),
        build_memo_choices(status_filter_val),
        "",
    )


# ================== Gradio 界面 ==================
with gr.Blocks(title="流萤 · 星穹铁道") as demo:
    with gr.Tabs():
        # ── Tab 1: 对话 ──
        with gr.TabItem("💬 对话"):
            with gr.Row():
                with gr.Column(scale=1, min_width=200):
                    gr.HTML(f"""
                    <div class="sidebar">
                        <div class="avatar">
                            <div class="glow"></div>
                            <img src="{avatar_img}" alt="流萤头像">
                        </div>
                        <div class="intro">流萤</div>
                        <div class="subtitle">星核猎手 · 萨姆驾驶员</div>
                        <div class="status-bar">
                            <span class="dot"></span>
                            在线 · 与你一起的悠闲时光
                        </div>
                        <div class="desc">
                            喜欢橡木蛋糕卷，对世界充满好奇。<br>
                            今天，想和你一起度过平凡的幸福。
                        </div>
                        <hr class="divider">
                        <div class="footer-text">✦ 来自《崩坏：星穹铁道》 ✦</div>
                    </div>
                    """)
                    gr.HTML("""
                    <div class="dark-toggle">
                        <button id="dark-mode-toggle" onclick="
                            const c = document.querySelector('.gradio-container');
                            const isDark = c.classList.toggle('dark-mode');
                            localStorage.setItem('chatbot-dark-mode', isDark ? '1' : '0');
                            this.textContent = isDark ? '☀️ 亮色模式' : '🌙 暗色模式';
                        ">🌙 暗色模式</button>
                    </div>
                    <div id="loading-overlay" class="loading-overlay">
                        <div class="loading-spinner"></div>
                        <div class="loading-text">流萤正在醒来……</div>
                    </div>
                    <div id="toast-container" class="toast-container"></div>
                    <script>
                    (function() {
                        // Dark mode persistence
                        if (localStorage.getItem('chatbot-dark-mode') === '1') {
                            document.querySelector('.gradio-container').classList.add('dark-mode');
                            var btn = document.getElementById('dark-mode-toggle');
                            if (btn) btn.textContent = '☀️ 亮色模式';
                        }
                    })();
                    // Toast helper
                    function showToast(msg, type) {
                        var c = document.getElementById('toast-container');
                        if (!c) return;
                        var t = document.createElement('div');
                        t.className = 'toast ' + (type || 'info');
                        t.textContent = msg;
                        c.appendChild(t);
                        setTimeout(function() { if (t.parentNode) t.remove(); }, 3000);
                    }
                    </script>
                    """)
                    with gr.Accordion("⚙️ 生成参数", open=False):
                        temperature = gr.Slider(0.1, 2.0, value=0.6, step=0.05, label="温度 (temperature)")
                        top_p = gr.Slider(0.1, 1.0, value=0.9, step=0.05, label="Top-p")
                        max_new_tokens = gr.Slider(64, 1024, value=300, step=16, label="最大生成长度")
                    with gr.Group(elem_classes="history-section"):
                        gr.Markdown("### 📜 历史对话")
                        history_dropdown = gr.Dropdown(
                            label="选择历史记录",
                            choices=[],
                            interactive=True,
                        )
                        with gr.Row():
                            load_btn = gr.Button("加载对话", size="sm")
                            delete_btn = gr.Button("🗑️ 删除", size="sm", elem_classes="delete-btn")
                            refresh_btn = gr.Button("刷新列表", size="sm")
                        history_status = gr.Textbox(label="", interactive=False, visible=False)

                with gr.Column(scale=3):
                    gr.Markdown("""
                    <div class="title-section">
                        <div class="stars">✦ ✦ ✦</div>
                        <h1>✨ 流萤 ✨</h1>
                        <p>与流萤一起度过悠闲时光，今天想聊些什么呢？</p>
                    </div>
                    """)
                    state = gr.State([])
                    pending_msg = gr.State("")
                    chatbot = gr.Chatbot(
                        label="对话记录",
                        elem_classes="chatbot",
                        render_markdown=True,
                        value=[{"role": "assistant", "content": "🦋 嗨，我是流萤……今天天气真好呢。想聊聊天吗？或者用语音跟我说说话吧。"}],
                    )
                    gr.HTML("""
                    <div id="typing-dots" class="typing-indicator" style="display:none">
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                    </div>
                    <script>
                    (function() {
                        var typingObs = new MutationObserver(function() {
                            var el = document.querySelector('.status textarea, .status input');
                            var dots = document.getElementById('typing-dots');
                            if (!dots) return;
                            var v = (el && el.value) || '';
                            dots.style.display = v.includes('生成') ? 'flex' : 'none';
                        });
                        var s = document.querySelector('.status');
                        if (s) typingObs.observe(s, { subtree: true, characterData: true, childList: true });
                    })();
                    </script>
                    """)
                    with gr.Row():
                        msg = gr.Textbox(label="输入你的消息", placeholder="对流萤说点什么吧...", scale=8)
                        audio_input = gr.Audio(sources=["microphone"], type="filepath", label="🎤 语音输入", scale=1)
                        send_btn = gr.Button("发送", variant="primary", scale=1)
                    with gr.Row():
                        selected_text = gr.Textbox(label="点击助手消息自动填充", scale=5, interactive=True)
                        gen_voice_btn = gr.Button("🔊 生成语音", variant="secondary", scale=1)
                        save_voice_btn = gr.Button("💾 保存语音", variant="secondary", scale=1)
                        stop_btn = gr.Button("⏹️ 停止", variant="stop", scale=1)
                    with gr.Row():
                        save_btn = gr.Button("💾 保存当前对话", elem_classes="secondary")
                        export_btn = gr.Button("📥 导出为 Markdown", elem_classes="secondary")
                        clear_btn = gr.Button("🗑️ 清空对话", elem_classes="secondary")
                        status = gr.Textbox(label="状态", interactive=False, value="就绪", elem_classes="status")
                    audio_output = gr.Audio(visible=True, autoplay=True, elem_classes="audio-hidden")
                    export_download = gr.File(label="下载导出的文件", visible=False)

        # ── Tab 2: 备忘录 ──
        with gr.TabItem("📋 备忘录"):
            gr.Markdown("### 📋 备忘录管理")
            with gr.Row():
                # 左侧：添加表单
                with gr.Column(scale=1):
                    gr.Markdown("#### ✏️ 添加备忘录")
                    memo_content = gr.Textbox(
                        label="内容",
                        placeholder="输入备忘录内容...",
                    )
                    with gr.Row():
                        memo_date = gr.Textbox(
                            label="日期 (YYYY-MM-DD)",
                            placeholder="2026-05-13",
                            scale=1,
                        )
                        memo_time = gr.Textbox(
                            label="时间 (HH:MM)",
                            placeholder="12:00",
                            scale=1,
                        )
                    memo_priority = gr.Radio(
                        choices=[("高优先级", "high"), ("中优先级", "medium"), ("低优先级", "low")],
                        value="medium",
                        label="优先级",
                    )
                    memo_add_btn = gr.Button("➕ 添加备忘录", variant="primary")
                    memo_status_msg = gr.Textbox(label="操作结果", interactive=False)

                # 右侧：备忘录列表
                with gr.Column(scale=2):
                    with gr.Row():
                        memo_status_filter = gr.Radio(
                            choices=[("待办", "pending"), ("已完成", "done"), ("全部", "all")],
                            value="pending",
                            label="筛选状态",
                        )
                        memo_refresh_btn = gr.Button("🔄 刷新", size="sm")

                    memo_cards = gr.HTML(render_memo_cards("pending"))

                    memo_selector = gr.Radio(
                        label="选择要操作的备忘录",
                        choices=build_memo_choices("pending"),
                        interactive=True,
                        elem_classes="memo-radio-group",
                    )
                    with gr.Row():
                        memo_toggle_btn = gr.Button("✅ 切换完成", size="sm", scale=1)
                        memo_delete_btn = gr.Button("🗑️ 删除", size="sm", scale=1)

    # ================== 对话事件绑定 ==================
    def capture(m):
        return m

    send_btn.click(capture, [msg], [pending_msg]).then(
        lambda: "", None, msg
    ).then(
        respond, [pending_msg, state, temperature, top_p, max_new_tokens, status],
        [state, chatbot, status]
    )

    msg.submit(capture, [msg], [pending_msg]).then(
        lambda: "", None, msg
    ).then(
        respond, [pending_msg, state, temperature, top_p, max_new_tokens, status],
        [state, chatbot, status]
    )

    stop_btn.click(request_stop, None, None)

    audio_input.change(set_voice_text, [audio_input, state], [msg, state])

    save_btn.click(save_history, [state, status], [history_status, status, history_dropdown])

    def do_export(h):
        path = export_history(h)
        if path:
            return gr.update(value=path, visible=True)
        return gr.update(visible=False)

    export_btn.click(do_export, [state], [export_download])
    clear_btn.click(clear, None, [state, chatbot, status])

    load_btn.click(load_history, [history_dropdown, state], [state, chatbot, status, history_dropdown])
    delete_btn.click(
        fn=delete_history,
        inputs=[history_dropdown, status],
        outputs=[history_status, status, history_dropdown],
        js="(dropdown, status) => confirm('确定要删除这条历史记录吗？')",
    )
    refresh_btn.click(refresh_history_list, None, history_dropdown)

    demo.load(refresh_history_list, None, history_dropdown)
    demo.load(None, None, None, js="""
    function() {
        var overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
            setTimeout(function() { if (overlay.parentNode) overlay.remove(); }, 500);
        }
    }
    """)

    gen_voice_btn.click(generate_voice_from_text, [selected_text], [audio_output, status])
    save_voice_btn.click(save_voice_from_text, [selected_text], [audio_output, status])

    chatbot.select(on_chat_select, [state], selected_text)

    # ================== 备忘录事件绑定 ==================
    memo_status_filter.change(
        _refresh_memo_ui, [memo_status_filter], [memo_cards, memo_selector, memo_status_msg]
    )

    memo_refresh_btn.click(
        _refresh_memo_ui, [memo_status_filter], [memo_cards, memo_selector, memo_status_msg]
    )

    memo_add_btn.click(
        add_memo_ui,
        [memo_content, memo_date, memo_time, memo_priority],
        [memo_cards, memo_status_msg],
    ).then(
        lambda f: build_memo_choices(f),
        [memo_status_filter],
        [memo_selector],
    ).then(
        lambda: "", None, memo_content
    ).then(
        lambda: "", None, memo_date
    ).then(
        lambda: "", None, memo_time
    )

    memo_toggle_btn.click(
        lambda a, s: memo_action("toggle", a, s),
        [memo_selector, memo_status_filter],
        [memo_cards, memo_status_msg, memo_selector],
    )

    memo_delete_btn.click(
        lambda a, s: memo_action("delete", a, s),
        [memo_selector, memo_status_filter],
        [memo_cards, memo_status_msg, memo_selector],
    )


# ================== 启动 ==================
validate_config()
cleanup_old_voices()
cleanup_old_histories()
load_model()

# 后台预加载常用语音
Thread(target=preload_common_audio, daemon=True).start()
# 启用 Gradio 队列，允许多事件并发
demo.queue(default_concurrency_limit=5)
demo.launch(share=False, css=custom_css)
restore_proxy()
