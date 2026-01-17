#!/usr/bin/env python3
"""
运行脚本 - 直接运行程序（不打包）

使用方法:
python run.py
"""
import subprocess
import sys
import os


def install_dependencies():
    """安装依赖"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_file = os.path.join(script_dir, "requirements.txt")

    if os.path.exists(requirements_file):
        print("正在安装依赖...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", requirements_file],
            check=True
        )
        print("依赖安装完成！\n")


def main():
    # 切换到脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # 检查是否需要安装依赖
    try:
        import PyQt6
    except ImportError:
        install_dependencies()

    # 运行主程序
    from main import main as run_app
    run_app()


if __name__ == "__main__":
    main()
