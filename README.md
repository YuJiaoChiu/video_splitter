# 视频智能分割器 Video Splitter

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PyQt6-6.4+-green.svg" alt="PyQt6">
  <img src="https://img.shields.io/badge/FFmpeg-required-orange.svg" alt="FFmpeg">
  <img src="https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-lightgrey.svg" alt="Platform">
</p>

一款智能视频分割工具，能够自动识别视频中的静音片段，并在静音处进行精准分割。适用于将长视频（如录播课程、会议录像、直播回放等）分割成多个较短的片段。

## 为什么需要这个工具？

- **传统分割方式的问题**：按固定时间点分割会导致语音被截断，观看体验差
- **智能分割的优势**：在静音处分割，确保每段视频的开头和结尾都是完整的语句

## 核心特性

### 智能静音检测
- 自动分析音频波形，识别静音区域
- 在目标时间点附近（可设置搜索范围）寻找最佳分割点
- 分割点选择在静音结束位置，确保下一段开头立即有声音

### 批量处理
- 支持整个文件夹的批量处理
- 自动递归扫描子文件夹中的视频
- 保持原有的目录结构

### 无损分割
- 使用 FFmpeg stream copy 模式
- 不重新编码，保持原视频画质
- 处理速度快，几乎不占用 CPU

### 灵活的输出选项
- **新建目录模式**：输出到新文件夹，同时复制非视频文件
- **覆盖模式**：直接替换原文件，节省磁盘空间

### 可自定义参数
| 参数 | 默认值 | 说明 |
|------|--------|------|
| 目标片段时长 | 30 分钟 | 每段视频的目标时长 |
| 搜索范围 | 10 分钟 | 在目标时间点前后搜索静音的范围 |
| 最小静音时长 | 1 秒 | 被识别为静音的最小持续时间 |

### 设置保存
- 一键保存当前设置
- 下次启动自动加载

## 分割逻辑示例

假设有一个 **69 分钟** 的视频，目标片段时长设为 **30 分钟**：

1. 计算需要分割成 2 段（69 ÷ 30 ≈ 2）
2. 目标分割点在 **34.5 分钟** 附近
3. 在 24.5 ~ 44.5 分钟范围内搜索静音区域
4. 找到 **32:15** 处有一段 1.5 秒的静音
5. 在静音结束位置（约 32:16.5）进行分割
6. 输出：`video-1.mp4`（32:16）和 `video-2.mp4`（36:44）

## 安装

### 系统要求
- Python 3.8 或更高版本
- FFmpeg（必须安装并添加到系统 PATH）

### 安装 FFmpeg

**macOS：**
```bash
brew install ffmpeg
```

**Windows：**
```bash
winget install ffmpeg
```

或从 [FFmpeg 官网](https://ffmpeg.org/download.html) 下载

### 安装依赖

```bash
git clone https://github.com/YuJiaoChiu/video_splitter.git
cd video_splitter
pip install -r requirements.txt
```

## 使用方法

### 方式一：直接运行

```bash
python main.py
```

或使用自动安装依赖的启动脚本：

```bash
python run.py
```

### 方式二：下载预编译版本

从 [Releases](https://github.com/YuJiaoChiu/video_splitter/releases) 页面下载：
- **macOS**：`VideoSplitter-macOS.dmg`
- **Windows**：`VideoSplitter.exe`

## 使用步骤

1. **选择文件夹**：拖拽包含视频的文件夹到窗口，或点击选择
2. **选择输出模式**：
   - 重新生成到新目录（推荐，更安全）
   - 覆盖源文件（节省空间，但不可逆）
3. **调整设置**（可选）：根据需要修改分割参数
4. **保存设置**（可选）：点击"保存设置"按钮保存当前配置
5. **开始处理**：点击"开始处理"按钮

## 支持的视频格式

- MP4 (.mp4)
- MKV (.mkv)
- AVI (.avi)
- MOV (.mov)
- WMV (.wmv)
- FLV (.flv)
- WebM (.webm)
- M4V (.m4v)
- MPEG (.mpeg, .mpg)

## 命名规则

分割后的文件按照 `原文件名-序号.扩展名` 格式命名：

```
原文件：lecture.mp4（90分钟）
分割后：
├── lecture-1.mp4（约30分钟）
├── lecture-2.mp4（约30分钟）
└── lecture-3.mp4（约30分钟）
```

## 自行打包

如需自行打包为可执行文件：

```bash
python build.py
```

输出位置：
- macOS：`dist/VideoSplitter`
- Windows：`dist/VideoSplitter.exe`

## 技术栈

- **GUI 框架**：PyQt6
- **视频处理**：FFmpeg
- **音频分析**：FFmpeg silencedetect 滤镜
- **打包工具**：PyInstaller

## 注意事项

1. **FFmpeg 必须安装**：程序启动时会检测，未安装会提示
2. **处理时间**：主要取决于视频时长和静音检测，分割本身很快
3. **磁盘空间**：新建目录模式需要足够的磁盘空间存放分割后的文件
4. **覆盖模式**：会删除原文件，请确保有备份

## 贡献

欢迎提交 Issue 和 Pull Request！

## License

MIT License
