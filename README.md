# 视频智能分割器 (Video Splitter)

根据音频静音自动分割长视频的桌面应用程序。

## 功能特点

- **智能分割**：在静音处自动寻找分割点，确保每段开头有声音
- **批量处理**：支持文件夹递归处理，保持原有目录结构
- **格式保持**：使用 stream copy 模式，保持原视频质量
- **两种输出模式**：
  - 重新生成到新目录（同时复制非视频文件）
  - 覆盖源文件
- **可自定义设置**：
  - 目标片段时长（默认30分钟）
  - 搜索范围（默认10分钟）
  - 最小静音时长（默认1秒）
- **设置保存**：保存设置后下次自动加载

## 系统要求

- Python 3.8+
- FFmpeg（必须安装并添加到 PATH）

### 安装 FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
```bash
winget install ffmpeg
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行程序

```bash
python run.py
```

或直接运行：
```bash
python main.py
```

## 打包为可执行文件

### macOS
```bash
python build.py
```
输出文件：`dist/VideoSplitter`

### Windows
```bash
python build.py
```
输出文件：`dist/VideoSplitter.exe`

## 使用说明

1. 拖拽包含视频的文件夹到程序窗口，或点击选择
2. 选择输出模式（新建目录/覆盖源文件）
3. 调整分割设置（可选）
4. 点击"保存设置"保存当前配置（可选）
5. 点击"开始处理"

## 命名规则

分割后的文件按照 `原文件名-序号` 命名：
- `video.mp4` → `video-1.mp4`, `video-2.mp4`, `video-3.mp4`

## 技术栈

- PyQt6 - GUI 框架
- FFmpeg - 视频处理
- PyInstaller - 打包工具

## License

MIT
