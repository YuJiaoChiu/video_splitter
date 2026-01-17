#!/usr/bin/env python3
"""
打包脚本 - 将程序打包成 exe

使用方法:
python build.py
"""
import subprocess
import sys
import os


def main():
    # 确保在正确的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("=" * 50)
    print("视频智能分割器 - 打包工具")
    print("=" * 50)

    # 检查依赖
    print("\n[1/3] 检查依赖...")
    try:
        import PyQt6
        print("  - PyQt6: OK")
    except ImportError:
        print("  - PyQt6: 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "PyQt6"], check=True)

    try:
        import PyInstaller
        print("  - PyInstaller: OK")
    except ImportError:
        print("  - PyInstaller: 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # 运行 PyInstaller
    print("\n[2/3] 正在打包...")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "build.spec", "--clean"],
        capture_output=False
    )

    if result.returncode != 0:
        print("\n打包失败！")
        sys.exit(1)

    # 完成
    print("\n[3/3] 打包完成！")
    print("\n" + "=" * 50)
    print("输出文件位置:")

    if sys.platform == "win32":
        exe_path = os.path.join(script_dir, "dist", "VideoSplitter.exe")
    else:
        exe_path = os.path.join(script_dir, "dist", "VideoSplitter")

    print(f"  {exe_path}")
    print("\n注意: 运行程序需要系统已安装 FFmpeg")
    print("=" * 50)


if __name__ == "__main__":
    main()
