"""UI 样式定义"""

custom_css = """
/* ===== CSS 变量（亮色模式默认） ===== */
:root {
    --bg-gradient: linear-gradient(135deg, #f0f4ff 0%, #fdf2f8 50%, #f0fdf4 100%);
    --sidebar-bg: rgba(255,255,255,0.88);
    --chatbot-bot-bg: white;
    --chatbot-bot-color: #334155;
    --chatbot-bot-border: #e2e8f0;
    --input-border: #e2e8f0;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --text-muted: #94a3b8;
    --btn-secondary-bg: white;
    --btn-secondary-color: #64748b;
    --btn-secondary-border: #e2e8f0;
    --status-bg: rgba(255,255,255,0.9);
    --shadow-sm: 0 2px 8px rgba(0,0,0,0.04);
    --shadow-md: 0 4px 24px rgba(0,0,0,0.05);
}

/* ===== 暗色模式 ===== */
.dark-mode {
    --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0c1222 100%);
    --sidebar-bg: rgba(30,41,59,0.92);
    --chatbot-bot-bg: #1e293b;
    --chatbot-bot-color: #e2e8f0;
    --chatbot-bot-border: #334155;
    --input-border: #475569;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --btn-secondary-bg: #1e293b;
    --btn-secondary-color: #94a3b8;
    --btn-secondary-border: #475569;
    --status-bg: rgba(30,41,59,0.9);
    --shadow-sm: 0 2px 8px rgba(0,0,0,0.2);
    --shadow-md: 0 4px 24px rgba(0,0,0,0.3);
}
.dark-mode .title-section {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%) !important;
}
.dark-mode .title-section h1 { text-shadow: 0 2px 12px rgba(0,0,0,0.4); }
.dark-mode input[type="text"],
.dark-mode textarea {
    background: #1e293b !important;
    color: #e2e8f0 !important;
}
.dark-mode .history-section { border-color: #334155 !important; }
.dark-mode .sidebar .avatar img { border-color: #334155; }

/* ===== 全局 ===== */
.gradio-container {
    background: var(--bg-gradient) !important;
    font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #c4b5fd; border-radius: 3px; }

/* ===== 标题 ===== */
.title-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 28px 30px;
    text-align: center;
    color: white;
    border-radius: 24px 24px 0 0;
    position: relative;
    overflow: hidden;
}
.title-section::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%; width: 200%; height: 200%;
    background: radial-gradient(circle at 30% 50%, rgba(255,255,255,0.12) 0%, transparent 50%),
                radial-gradient(circle at 70% 50%, rgba(255,255,255,0.08) 0%, transparent 50%);
    animation: shimmer 6s ease-in-out infinite;
}
@keyframes shimmer {
    0%, 100% { transform: translate(0, 0); }
    50% { transform: translate(8px, -8px); }
}
.title-section h1 {
    font-size: 2.5rem; margin: 0; font-weight: 700;
    position: relative; z-index: 1;
    text-shadow: 0 2px 12px rgba(0,0,0,0.15);
}
.title-section p {
    font-size: 1rem; opacity: 0.95; margin: 10px 0 0;
    position: relative; z-index: 1;
}
.title-section .stars {
    position: absolute; top: 10px; right: 20px;
    font-size: 1.2rem; opacity: 0.4; z-index: 1;
}

/* ===== 暗色模式切换按钮 ===== */
.dark-toggle {
    text-align: center; margin: 8px 0;
}
.dark-toggle button {
    background: transparent !important;
    border: 1px solid var(--btn-secondary-border) !important;
    border-radius: 20px !important;
    padding: 4px 16px !important;
    font-size: 0.8rem !important;
    color: var(--text-secondary) !important;
    cursor: pointer;
    transition: all 0.2s;
}
.dark-toggle button:hover {
    background: rgba(167,139,250,0.1) !important;
}

/* ===== 侧边栏 ===== */
.sidebar {
    background: var(--sidebar-bg);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 24px 20px;
    height: 100%;
    box-shadow: var(--shadow-md);
}
.sidebar .avatar {
    display: flex; justify-content: center; align-items: center;
    margin-bottom: 16px; position: relative;
}
.sidebar .avatar .glow {
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 140px; height: 140px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2, #34d399);
    opacity: 0.4;
    animation: glow-pulse 3s ease-in-out infinite;
}
@keyframes glow-pulse {
    0%, 100% { opacity: 0.4; transform: translate(-50%, -50%) scale(1); }
    50% { opacity: 0.7; transform: translate(-50%, -50%) scale(1.06); }
}
.sidebar .avatar img {
    width: 120px; height: 120px;
    border-radius: 50%;
    border: 3px solid white;
    box-shadow: 0 4px 16px rgba(102,126,234,0.3);
    object-fit: cover;
    position: relative; z-index: 1;
}
.sidebar .intro {
    text-align: center;
    font-size: 1.25rem; font-weight: 600;
    color: var(--text-primary); margin-bottom: 4px;
}
.sidebar .subtitle {
    text-align: center;
    font-size: 0.8rem; color: var(--text-muted);
    margin-bottom: 16px;
}
.sidebar .status-bar {
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 16px; font-size: 0.85rem; color: var(--text-secondary);
}
.sidebar .status-bar .dot {
    width: 8px; height: 8px;
    background: #34d399; border-radius: 50%;
    margin-right: 6px;
    animation: dot-blink 2s ease-in-out infinite;
}
@keyframes dot-blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}
.sidebar .desc {
    color: var(--text-secondary); font-size: 0.88rem;
    line-height: 1.7; text-align: center;
}
.sidebar .divider {
    border: none; height: 1px;
    background: linear-gradient(to right, transparent, #e2e8f0, transparent);
    margin: 16px 0;
}
.sidebar .footer-text {
    font-size: 0.75rem; color: var(--text-muted); text-align: center;
}

/* ===== 历史对话 ===== */
.history-section {
    background: var(--sidebar-bg);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(226,232,240,0.6);
    border-radius: 14px;
    padding: 16px;
    margin-top: 16px;
}
.dark-mode .history-section { border-color: rgba(71,85,105,0.6); }

/* 历史按钮组无缝拼接 */
.history-section .row .column:first-child button {
    border-radius: 28px 0 0 28px !important;
}
.history-section .row .column:last-child button {
    border-radius: 0 28px 28px 0 !important;
}
.history-section .row .column:not(:first-child):not(:last-child) button {
    border-radius: 0 !important;
    border-left: none !important;
    border-right: none !important;
}
.history-section .row .column:first-child button {
    border-right: none !important;
}

/* ===== 聊天气泡 ===== */
.chatbot {
    min-height: 420px;
}
.chatbot .user, .chatbot .bot {
    padding: 10px 18px !important;
    max-width: 80% !important;
    word-break: break-word !important;
}
.chatbot .user {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: white !important;
    border-radius: 20px 20px 4px 20px !important;
    box-shadow: 0 2px 8px rgba(102,126,234,0.25) !important;
}
.chatbot .bot {
    background: var(--chatbot-bot-bg) !important;
    color: var(--chatbot-bot-color) !important;
    border-radius: 20px 20px 20px 4px !important;
    border: 1px solid var(--chatbot-bot-border) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ===== 输入框 ===== */
input[type="text"], textarea {
    border-radius: 40px !important;
    border: 2px solid var(--input-border) !important;
    background: white !important;
    padding: 12px 24px !important;
    font-size: 1rem !important;
    transition: all 0.2s ease !important;
}
input[type="text"]:focus, textarea:focus {
    border-color: #a78bfa !important;
    box-shadow: 0 2px 12px rgba(167,139,250,0.15) !important;
    outline: none !important;
}

/* ===== 按钮 ===== */
button.primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    border-radius: 40px !important;
    padding: 10px 28px !important;
    font-weight: 600 !important;
    color: white !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 14px rgba(102,126,234,0.3) !important;
}
button.primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(102,126,234,0.4) !important;
}
button.secondary {
    background: var(--btn-secondary-bg) !important;
    color: var(--btn-secondary-color) !important;
    border: 1px solid var(--btn-secondary-border) !important;
    border-radius: 40px !important;
    padding: 8px 20px !important;
    transition: all 0.2s ease !important;
}
button.secondary:hover {
    background: #f8fafc !important;
    border-color: #cbd5e1 !important;
    transform: translateY(-1px) !important;
}
.dark-mode button.secondary:hover {
    background: #334155 !important;
    border-color: #64748b !important;
}
button.stop {
    background: linear-gradient(135deg, #f87171, #dc2626) !important;
    color: white !important;
    border: none !important;
    border-radius: 40px !important;
    transition: all 0.2s ease !important;
}
button.stop:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(220,38,38,0.3) !important;
}

/* ===== 删除按钮（与 secondary 同尺寸，红色文字） ===== */
button.delete-btn {
    background: var(--btn-secondary-bg) !important;
    color: #ef4444 !important;
    border: 1px solid var(--btn-secondary-border) !important;
    border-radius: 40px !important;
    padding: 8px 20px !important;
    font-size: 0.88rem !important;
    transition: all 0.2s ease !important;
}
button.delete-btn:hover {
    background: #fef2f2 !important;
    border-color: #fca5a5 !important;
}

/* ===== 状态栏 ===== */
.status {
    background: var(--status-bg) !important;
    border: 1px solid var(--input-border) !important;
    border-radius: 30px !important;
    padding: 5px 18px !important;
    font-size: 0.85rem !important;
    color: var(--text-secondary) !important;
    text-align: center !important;
}

/* ===== 移动端适配 ===== */
@media (max-width: 768px) {
    .gradio-container .grid-wrap { gap: 8px !important; }
    .title-section { padding: 16px !important; border-radius: 16px 16px 0 0 !important; }
    .title-section h1 { font-size: 1.6rem !important; }
    .title-section p { font-size: 0.85rem !important; }
    .sidebar { padding: 16px 12px !important; }
    .sidebar .avatar img { width: 80px; height: 80px; }
    .sidebar .avatar .glow { width: 100px; height: 100px; }
    .sidebar .intro { font-size: 1rem; }
    .chatbot .user, .chatbot .bot { max-width: 90% !important; font-size: 0.85rem !important; }
    .chatbot { min-height: 300px; }
    input[type="text"], textarea { padding: 8px 16px !important; font-size: 0.88rem !important; }
    button.primary { padding: 8px 18px !important; font-size: 0.85rem !important; }
}
"""
