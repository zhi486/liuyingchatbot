
# 流萤 · 星穹铁道聊天机器人 ✨

基于 Qwen2-7B 大语言模型，通过 Gradio 构建的《崩坏：星穹铁道》角色「流萤」对话机器人。支持语音输入、流萤语音回复、天气查询、对话历史保存等功能，让你与流萤共度闲暇时光。

![演示截图](https://via.placeholder.com/800x400?text=Demo+Screenshot+Coming+Soon)

## ✨ 功能特性

- 🧠 **本地大模型**：使用 Qwen2-7B-Instruct 模型，4-bit 量化，在消费级显卡上流畅运行
- 🎙️ **语音输入**：通过百度语音 API 将语音转换为文字
- 🔊 **流萤语音回复**：使用 Fish Audio 合成流萤角色声音，支持缓存和手动生成/保存
- ☁️ **天气查询**：输入“城市+天气”即可查询实时天气
- 💾 **对话历史**：保存、加载、删除聊天记录
- 🖼️ **流萤头像**：自定义角色头像（支持 base64 或 URL）
- 🌐 **简洁 Web 界面**：基于 Gradio，开箱即用

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 至少 8GB 显存（推荐 10GB+）或 16GB 内存
- ffmpeg（用于音频格式转换）
- 可访问互联网（语音合成、语音识别、天气查询需要）

### 1. 克隆仓库
```bash
git clone https://github.com/zhi486/liuyingchatbot.git
cd liuyingchatbot
2. 安装依赖
bash
pip install -r requirements.txt
3. 配置环境变量
复制 .env.example 为 .env 并填写真实配置：

bash
cp .env.example .env
编辑 .env，填入你的 API 密钥和路径：

ini
# 百度语音（必填）
BAIDU_APP_ID=你的APP_ID
BAIDU_API_KEY=你的API_KEY
BAIDU_SECRET_KEY=你的SECRET_KEY

# Fish Audio（必填）
FISH_API_KEY=你的Fish_API_Key
LIUYING_REFERENCE_ID=你的角色参考ID

# 代理（可选）
PROXY_URL=http://127.0.0.1:7890

# 模型路径（必填，可相对路径）
MODEL_PATH=./models/Qwen2-7B-Instruct

# ffmpeg 路径（可选，若已加入系统 PATH 可留空）
FFMPEG_PATH=C:/ffmpeg/bin
注意：请勿将 .env 提交到 GitHub，它已包含在 .gitignore 中。

4. 下载模型
从 Hugging Face 下载 Qwen2-7B-Instruct 模型，并放置在 MODEL_PATH 指定的目录下。

模型地址：Qwen/Qwen2-7B-Instruct

也可以使用其他兼容的 Qwen 模型（如 Qwen2-1.5B、Qwen2-72B），但可能需要调整显存和生成参数。

5. 安装 ffmpeg
Windows：从 ffmpeg.org 下载，解压后将 bin 目录添加到系统 PATH 或配置 FFMPEG_PATH。

macOS：brew install ffmpeg

Linux：sudo apt install ffmpeg

6. 运行
bash
python web_chatbot_voice4.py
浏览器自动打开 http://127.0.0.1:7860，即可与流萤对话。

🧭 使用指南
基本对话
在输入框输入文字，点击“发送”或按回车即可得到流萤的回复。

支持语音输入：点击麦克风图标录制语音，系统会自动识别并发送。

语音回复
点击任意一条流萤的回复，其内容会自动填充到下方的文本框中。

点击“🔊 生成语音”按钮，合成该条消息的语音并自动播放（支持缓存，重复点击直接播放）。

点击“💾 保存语音”按钮，将语音保存到 voices/ 目录下。

天气查询
在输入框中直接输入“城市+天气”，例如：“上海天气”、“北京的天气怎么样”，机器人会调用天气 API 返回实时天气。

对话历史
保存：点击“💾 保存当前对话”，对话内容会以 JSON 格式保存到 histories/ 目录。

加载：从右侧下拉列表选择历史记录，点击“加载对话”即可恢复。

删除：选中记录后点击“🗑️ 删除”。

刷新：点击“刷新列表”更新下拉选项。

📁 文件结构
text
.
├── web_chatbot_voice4.py   # 主程序
├── liuying_avatar.png      # 流萤头像
├── .env.example            # 环境变量模板
├── .gitignore              # Git 忽略文件
├── requirements.txt        # Python 依赖
├── README.md               # 项目说明
├── histories/              # 对话历史存储目录（自动创建）
├── voices/                 # 保存的语音文件目录（自动创建）
└── models/                 # 模型存放目录（需手动放置）
❓ 常见问题
1. 运行时报错 ModuleNotFoundError: No module named 'dotenv'
请安装 python-dotenv：pip install python-dotenv

2. 语音识别失败或语音合成失败
检查百度语音、Fish Audio 的 API 密钥是否正确且余额充足。

检查网络代理设置，可能需要配置 PROXY_URL。

检查 ffmpeg 是否正确安装。

3. 模型加载失败或显存不足
确保模型路径正确。

可尝试降低量化配置（如从 4-bit 改为 8-bit），或使用更小的模型（如 Qwen2-1.5B）。

4. 天气查询失败
天气 API 可能需要代理，请确保 PROXY_URL 配置正确。

某些城市可能无法解析，请尝试输入更具体的城市名（如“北京市”）。

📝 许可证
本项目采用 MIT License 开源协议，允许自由使用和修改，但需保留版权声明。

🙏 致谢
模型：Qwen2 系列

语音识别：百度语音

语音合成：Fish Audio

天气数据：Open-Meteo

地理编码：Nominatim

界面框架：Gradio

🌟 如果你喜欢这个项目，欢迎给个 Star！
若有问题或建议，请提交 Issue 或 Pull Request。

text

### 使用说明
1. 将以上内容保存为 `README.md` 文件，放在项目根目录。
2. 如果需要添加截图，可以替换 `![演示截图]` 部分的链接为实际图片 URL（建议使用 GitHub 仓库中的图片路径）。
3. 根据实际功能微调内容（如未实现的特性可以删除）。
4. 提交到 GitHub：
   ```bash
   git add README.md
   git commit -m "添加 README"
   git push
如果未来需要增加更多细节（如 Docker 部署、贡献指南），可继续完善。祝开源顺利！
