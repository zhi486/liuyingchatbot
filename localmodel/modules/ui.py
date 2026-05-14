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
/* ===== 备忘录模块 ===== */
.memo-form-wrap {
    background: var(--sidebar-bg);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 16px;
    box-shadow: var(--shadow-md);
}
.memo-filter-row {
    display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap;
}
.memo-filter-row label {
    display: flex; align-items: center; gap: 8px;
    padding: 6px 18px; border-radius: 28px;
    cursor: pointer; font-size: 0.85rem;
    transition: all 0.2s;
    background: var(--sidebar-bg);
    border: 1px solid var(--input-border);
    color: var(--text-secondary);
}
.memo-filter-row label:hover { border-color: #a78bfa; }
.memo-filter-row label.selected {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white; border-color: transparent;
}
.memo-filter-row input[type="radio"] { display: none; }
.memo-actions-bar {
    display: flex; gap: 10px; align-items: flex-end;
    margin-bottom: 20px; flex-wrap: wrap;
}
.memo-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 14px;
}
.memo-card {
    display: flex;
    background: var(--sidebar-bg);
    border-radius: 14px; overflow: hidden;
    box-shadow: var(--shadow-sm);
    transition: all 0.25s ease;
    border: 1px solid var(--input-border);
}
.memo-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-md);
}
.memo-priority {
    width: 5px; flex-shrink: 0;
    border-radius: 14px 0 0 14px;
}
.memo-body {
    flex: 1; padding: 16px 18px;
    display: flex; flex-direction: column; gap: 10px;
}
.memo-content {
    font-size: 1rem; font-weight: 600;
    color: var(--text-primary); line-height: 1.5;
    word-break: break-word;
}
.memo-meta {
    display: flex; gap: 10px; align-items: center;
    flex-wrap: wrap; font-size: 0.8rem; color: var(--text-muted);
}
.memo-date { color: var(--text-secondary); }
.memo-badge {
    padding: 2px 12px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600;
}
.memo-badge.pending { background: rgba(245,158,11,0.12); color: #d97706; }
.memo-badge.done { background: rgba(52,211,153,0.12); color: #059669; }
.memo-badge.cancelled { background: rgba(156,163,175,0.12); color: #6b7280; }
.memo-pill {
    padding: 2px 10px; border-radius: 14px;
    font-size: 0.72rem;
    background: rgba(167,139,250,0.08);
    color: var(--text-muted);
    border: 1px solid var(--input-border);
}
.memo-empty {
    text-align: center; padding: 60px 20px;
    font-size: 1.1rem; color: var(--text-muted);
    background: var(--sidebar-bg); border-radius: 16px;
    border: 2px dashed var(--input-border);
}
.dark-mode .memo-badge.pending { background: rgba(245,158,11,0.2); color: #fbbf24; }
.dark-mode .memo-badge.done { background: rgba(52,211,153,0.2); color: #34d399; }
.dark-mode .memo-badge.cancelled { background: rgba(156,163,175,0.15); color: #9ca3af; }
.dark-mode .memo-card { border-color: rgba(71,85,105,0.6); }
.dark-mode .memo-empty { border-color: rgba(71,85,105,0.5); }
.dark-mode .memo-filter-row label.selected {
    background: linear-gradient(135deg, #7c3aed, #a855f7);
}
.dark-mode .memo-pill {
    background: rgba(167,139,250,0.1);
    border-color: rgba(71,85,105,0.5); color: #c4b5fd;
}
/* ===== 备忘录单选组（类似卡片选择器） ===== */
.memo-radio-group {
    display: flex; flex-direction: column; gap: 6px;
    max-height: 280px; overflow-y: auto;
    padding: 8px;
    background: var(--sidebar-bg);
    border-radius: 14px;
    border: 1px solid var(--input-border);
    margin-bottom: 12px;
}
.memo-radio-group label {
    display: flex !important; align-items: center !important; gap: 10px !important;
    padding: 10px 14px !important;
    border-radius: 10px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    border: 1px solid transparent !important;
    background: rgba(255,255,255,0.4) !important;
    margin: 0 !important;
}
.memo-radio-group label:hover {
    background: rgba(167,139,250,0.08) !important;
    border-color: #c4b5fd !important;
}
.memo-radio-group label.selected {
    background: linear-gradient(135deg, rgba(102,126,234,0.12), rgba(118,75,162,0.12)) !important;
    border-color: #a78bfa !important;
    box-shadow: 0 0 0 2px rgba(167,139,250,0.2) !important;
}
.memo-radio-group input[type="radio"] {
    accent-color: #7c3aed !important;
    width: 16px; height: 16px;
    flex-shrink: 0;
}
.dark-mode .memo-radio-group {
    background: rgba(30,41,59,0.5);
    border-color: rgba(71,85,105,0.6);
}
.dark-mode .memo-radio-group label {
    background: rgba(30,41,59,0.4) !important;
}
.dark-mode .memo-radio-group label:hover {
    background: rgba(167,139,250,0.1) !important;
}
.dark-mode .memo-radio-group label.selected {
    background: rgba(124,58,237,0.15) !important;
    border-color: #7c3aed !important;
}
@media (max-width: 768px) {
    .memo-grid { grid-template-columns: 1fr; }
    .memo-actions-bar { flex-direction: column; }
    .memo-card .memo-content { font-size: 0.92rem; }
}

/* ===== 加载遮罩 ===== */
.loading-overlay {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(255,255,255,0.92);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    z-index: 9999; transition: opacity 0.4s ease;
}
.dark-mode .loading-overlay { background: rgba(15,23,42,0.94); }
.loading-overlay.hidden {
    opacity: 0; pointer-events: none; visibility: hidden;
}
.loading-spinner {
    width: 48px; height: 48px;
    border: 3px solid #e2e8f0;
    border-top-color: #667eea;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}
.dark-mode .loading-spinner { border-color: #334155; border-top-color: #a78bfa; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading-text {
    margin-top: 16px; font-size: 0.95rem; color: #64748b;
    font-family: 'Segoe UI', 'Roboto', sans-serif;
}
.dark-mode .loading-text { color: #94a3b8; }

/* ===== 打字指示器（三个跳动圆点） ===== */
.typing-indicator {
    display: flex; align-items: center; gap: 6px;
    padding: 10px 18px;
}
.typing-dot {
    width: 8px; height: 8px;
    background: #a78bfa; border-radius: 50%;
    animation: typing-bounce 1.4s ease-in-out infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing-bounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
    30% { transform: translateY(-8px); opacity: 1; }
}

/* ===== Toast 通知 ===== */
.toast-container {
    position: fixed; top: 20px; right: 20px; z-index: 10000;
    display: flex; flex-direction: column; gap: 8px;
}
.toast {
    padding: 12px 24px; border-radius: 14px;
    font-size: 0.9rem; font-weight: 500;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    animation: toast-in 0.35s ease, toast-out 0.35s ease 2.5s forwards;
    max-width: 380px;
}
.toast.success { background: rgba(52,211,153,0.92); color: #065f46; }
.toast.error { background: rgba(248,113,113,0.92); color: #991b1b; }
.toast.info { background: rgba(167,139,250,0.92); color: #4c1d95; }
.dark-mode .toast.success { background: rgba(52,211,153,0.85); color: #d1fae5; }
.dark-mode .toast.error { background: rgba(248,113,113,0.85); color: #fee2e2; }
.dark-mode .toast.info { background: rgba(167,139,250,0.85); color: #ede9fe; }
@keyframes toast-in { from { opacity: 0; transform: translateX(60px); } to { opacity: 1; transform: translateX(0); } }
@keyframes toast-out { from { opacity: 1; } to { opacity: 0; transform: translateY(-10px); } }

/* ===== 状态栏颜色编码 ===== */
.status.ready { color: #059669 !important; border-color: rgba(52,211,153,0.3) !important; }
.status.processing { color: #d97706 !important; border-color: rgba(245,158,11,0.4) !important; }
.status.stopped { color: #6366f1 !important; border-color: rgba(99,102,241,0.3) !important; }
.status.error { color: #dc2626 !important; border-color: rgba(220,38,38,0.3) !important; }
.dark-mode .status.ready { color: #34d399 !important; }
.dark-mode .status.processing { color: #fbbf24 !important; }
.dark-mode .status.stopped { color: #a78bfa !important; }
.dark-mode .status.error { color: #fca5a5 !important; }

/* ===== 欢迎占位 ===== */
.welcome-placeholder {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    min-height: 360px; text-align: center; padding: 40px;
}
.welcome-placeholder .welcome-icon {
    font-size: 3.5rem; margin-bottom: 16px;
    animation: welcome-float 3s ease-in-out infinite;
}
@keyframes welcome-float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}
.welcome-placeholder .welcome-title {
    font-size: 1.4rem; font-weight: 700;
    color: var(--text-primary); margin-bottom: 8px;
}
.welcome-placeholder .welcome-hint {
    font-size: 0.9rem; color: var(--text-muted);
    max-width: 360px; line-height: 1.6;
}

/* ===== 增强移动端 ===== */
@media (max-width: 640px) {
    .toast-container { left: 12px; right: 12px; }
    .toast { max-width: 100%; }
    .loading-text { font-size: 0.85rem; }
    .gradio-container .tabs > .tab-nav button {
        font-size: 0.8rem !important; padding: 6px 12px !important;
    }
}

/* ===== 对话区域过渡动画 ===== */
.chatbot .message {
    animation: msg-in 0.3s ease;
}
@keyframes msg-in {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

"""
