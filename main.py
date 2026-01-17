#!/usr/bin/env python3
"""
视频智能分割器 - 主程序入口

根据音频静音自动分割长视频
"""
import sys
import os

# 确保可以导入本地模块
if getattr(sys, 'frozen', False):
    # 打包后的路径
    base_path = sys._MEIPASS
else:
    # 开发时的路径
    base_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base_path)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.main_window import MainWindow


def check_ffmpeg() -> bool:
    """检查 FFmpeg 是否可用"""
    import subprocess
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True
        )
        subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def main():
    """主函数"""
    # 检查 FFmpeg
    if not check_ffmpeg():
        from PyQt6.QtWidgets import QMessageBox
        app = QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "错误",
            "未检测到 FFmpeg！\n\n"
            "请确保已安装 FFmpeg 并添加到系统 PATH 中。\n\n"
            "下载地址: https://ffmpeg.org/download.html\n\n"
            "Windows 用户可以使用 winget 安装:\n"
            "winget install ffmpeg\n\n"
            "macOS 用户可以使用 Homebrew 安装:\n"
            "brew install ffmpeg"
        )
        sys.exit(1)

    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("视频智能分割器")
    app.setOrganizationName("VideoSplitter")

    # 设置默认字体
    font = QFont()
    font.setFamily("Microsoft YaHei")
    font.setPointSize(10)
    app.setFont(font)

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
