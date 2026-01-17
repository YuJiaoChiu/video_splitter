"""
文件管理模块 - 处理文件夹遍历、复制等操作
"""
import os
import shutil
from typing import List, Optional, Callable, Generator, Tuple
from dataclasses import dataclass
from enum import Enum


class OutputMode(Enum):
    """输出模式"""
    NEW = "new"          # 输出到新目录
    OVERWRITE = "overwrite"  # 覆盖源文件


@dataclass
class VideoFile:
    """视频文件信息"""
    path: str
    relative_path: str  # 相对于源目录的路径
    size: int  # 文件大小（字节）

    @property
    def filename(self) -> str:
        return os.path.basename(self.path)

    @property
    def directory(self) -> str:
        return os.path.dirname(self.path)

    @property
    def size_str(self) -> str:
        """格式化的文件大小"""
        size = self.size
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"


class FileManager:
    """文件管理器"""

    VIDEO_EXTENSIONS = (
        ".mp4", ".mkv", ".avi", ".mov", ".wmv",
        ".flv", ".webm", ".m4v", ".mpeg", ".mpg"
    )

    def __init__(self, video_extensions: Optional[tuple] = None):
        """
        初始化文件管理器

        Args:
            video_extensions: 支持的视频扩展名
        """
        self.video_extensions = video_extensions or self.VIDEO_EXTENSIONS

    def is_video_file(self, path: str) -> bool:
        """检查是否为视频文件"""
        ext = os.path.splitext(path)[1].lower()
        return ext in self.video_extensions

    def scan_directory(
        self,
        directory: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[VideoFile]:
        """
        递归扫描目录中的所有视频文件

        Args:
            directory: 目录路径
            progress_callback: 进度回调函数

        Returns:
            视频文件列表
        """
        video_files = []
        directory = os.path.abspath(directory)

        for root, dirs, files in os.walk(directory):
            for filename in files:
                if self.is_video_file(filename):
                    full_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(full_path, directory)

                    if progress_callback:
                        progress_callback(f"发现: {relative_path}")

                    try:
                        size = os.path.getsize(full_path)
                    except OSError:
                        size = 0

                    video_files.append(VideoFile(
                        path=full_path,
                        relative_path=relative_path,
                        size=size
                    ))

        return video_files

    def get_output_path(
        self,
        video_file: VideoFile,
        source_dir: str,
        output_dir: str,
        output_mode: OutputMode
    ) -> str:
        """
        获取输出目录路径

        Args:
            video_file: 视频文件
            source_dir: 源目录
            output_dir: 输出目录（仅在 NEW 模式下使用）
            output_mode: 输出模式

        Returns:
            输出目录路径
        """
        if output_mode == OutputMode.OVERWRITE:
            return video_file.directory
        else:
            # 保持相对目录结构
            relative_dir = os.path.dirname(video_file.relative_path)
            return os.path.join(output_dir, relative_dir)

    def copy_non_video_files(
        self,
        source_dir: str,
        output_dir: str,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ):
        """
        复制非视频文件到输出目录（保持目录结构）

        Args:
            source_dir: 源目录
            output_dir: 输出目录
            progress_callback: 进度回调函数
        """
        source_dir = os.path.abspath(source_dir)
        output_dir = os.path.abspath(output_dir)

        # 收集所有非视频文件
        files_to_copy = []
        for root, dirs, files in os.walk(source_dir):
            for filename in files:
                if not self.is_video_file(filename):
                    full_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(full_path, source_dir)
                    files_to_copy.append((full_path, relative_path))

        if not files_to_copy:
            return

        # 复制文件
        total = len(files_to_copy)
        for i, (src_path, rel_path) in enumerate(files_to_copy):
            dst_path = os.path.join(output_dir, rel_path)
            dst_dir = os.path.dirname(dst_path)

            # 创建目标目录
            os.makedirs(dst_dir, exist_ok=True)

            # 复制文件
            if progress_callback:
                progress_callback(f"复制: {rel_path}", (i + 1) / total)

            try:
                shutil.copy2(src_path, dst_path)
            except (IOError, OSError) as e:
                print(f"复制文件失败: {rel_path} - {e}")

    def delete_original_video(self, video_path: str) -> bool:
        """
        删除原始视频文件

        Args:
            video_path: 视频文件路径

        Returns:
            是否删除成功
        """
        try:
            os.remove(video_path)
            return True
        except OSError:
            return False

    def ensure_directory(self, directory: str):
        """确保目录存在"""
        os.makedirs(directory, exist_ok=True)

    def get_unique_output_dir(self, base_dir: str) -> str:
        """
        获取唯一的输出目录名

        如果目录已存在，添加数字后缀

        Args:
            base_dir: 基础目录路径

        Returns:
            唯一的目录路径
        """
        if not os.path.exists(base_dir):
            return base_dir

        counter = 1
        while True:
            new_dir = f"{base_dir}_{counter}"
            if not os.path.exists(new_dir):
                return new_dir
            counter += 1

    def calculate_total_size(self, video_files: List[VideoFile]) -> int:
        """计算视频文件总大小"""
        return sum(vf.size for vf in video_files)

    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        size = size_bytes
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
