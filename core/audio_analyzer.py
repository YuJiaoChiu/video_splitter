"""
音频分析模块 - 用于检测视频中的静音区域
"""
import os
import tempfile
import subprocess
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass


@dataclass
class SilenceRegion:
    """静音区域"""
    start: float  # 开始时间（秒）
    end: float    # 结束时间（秒）

    @property
    def duration(self) -> float:
        return self.end - self.start

    @property
    def center(self) -> float:
        return (self.start + self.end) / 2


class AudioAnalyzer:
    """音频分析器 - 检测静音区域"""

    def __init__(
        self,
        silence_threshold_db: int = -40,
        min_silence_duration: float = 0.5
    ):
        """
        初始化音频分析器

        Args:
            silence_threshold_db: 静音阈值（dBFS），低于此值视为静音
            min_silence_duration: 最小静音持续时间（秒）
        """
        self.silence_threshold_db = silence_threshold_db
        self.min_silence_duration = min_silence_duration

    def get_video_duration(self, video_path: str) -> float:
        """
        获取视频时长（秒）

        Args:
            video_path: 视频文件路径

        Returns:
            视频时长（秒）
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError) as e:
            raise RuntimeError(f"无法获取视频时长: {e}")

    def detect_silence_regions(
        self,
        video_path: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[SilenceRegion]:
        """
        检测视频中的静音区域

        使用 FFmpeg 的 silencedetect 滤镜

        Args:
            video_path: 视频文件路径
            start_time: 开始时间（秒），None表示从头开始
            end_time: 结束时间（秒），None表示到结尾
            progress_callback: 进度回调函数

        Returns:
            静音区域列表
        """
        cmd = ["ffmpeg", "-hide_banner"]

        # 设置起始时间
        if start_time is not None:
            cmd.extend(["-ss", str(start_time)])

        cmd.extend(["-i", video_path])

        # 设置结束时间
        if end_time is not None:
            if start_time is not None:
                duration = end_time - start_time
            else:
                duration = end_time
            cmd.extend(["-t", str(duration)])

        # 使用 silencedetect 滤镜
        cmd.extend([
            "-af", f"silencedetect=noise={self.silence_threshold_db}dB:d={self.min_silence_duration}",
            "-f", "null",
            "-"
        ])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            # silencedetect 输出在 stderr
            output = result.stderr
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"音频分析失败: {e}")

        # 解析输出
        regions = self._parse_silence_output(output)

        # 调整时间偏移（如果指定了start_time）
        if start_time is not None and start_time > 0:
            regions = [
                SilenceRegion(r.start + start_time, r.end + start_time)
                for r in regions
            ]

        return regions

    def _parse_silence_output(self, output: str) -> List[SilenceRegion]:
        """
        解析 FFmpeg silencedetect 输出

        输出格式:
        [silencedetect @ ...] silence_start: 10.5
        [silencedetect @ ...] silence_end: 12.3 | silence_duration: 1.8
        """
        regions = []
        current_start = None

        for line in output.split("\n"):
            if "silence_start:" in line:
                try:
                    parts = line.split("silence_start:")
                    current_start = float(parts[1].strip().split()[0])
                except (IndexError, ValueError):
                    continue

            elif "silence_end:" in line and current_start is not None:
                try:
                    parts = line.split("silence_end:")
                    end_part = parts[1].strip().split()[0]
                    end_time = float(end_part)
                    regions.append(SilenceRegion(current_start, end_time))
                    current_start = None
                except (IndexError, ValueError):
                    continue

        return regions

    def find_silence_near_target(
        self,
        video_path: str,
        target_time: float,
        search_range: float = 60.0,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Optional[float]:
        """
        在目标时间点附近寻找最佳静音分割点

        选择静音区域的结束位置作为分割点，这样：
        - 前一段结尾会有静音
        - 后一段开头马上就有声音

        Args:
            video_path: 视频文件路径
            target_time: 目标分割时间（秒）
            search_range: 搜索范围（秒），在目标时间前后各搜索这么长时间
            progress_callback: 进度回调函数

        Returns:
            最佳分割时间点（静音区域的结束位置），如果没找到则返回None
        """
        # 计算搜索范围
        start_time = max(0, target_time - search_range)
        end_time = target_time + search_range

        # 检测静音区域
        regions = self.detect_silence_regions(
            video_path,
            start_time=start_time,
            end_time=end_time,
            progress_callback=progress_callback
        )

        if not regions:
            return None

        # 找到距离目标时间最近的静音区域
        best_region = min(
            regions,
            key=lambda r: abs(r.center - target_time)
        )

        # 返回静音区域的结束位置，这样下一段开头就有声音
        return best_region.end

    def calculate_split_points(
        self,
        video_path: str,
        target_segment_duration: float = 1800,
        search_range: float = 60.0,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> List[float]:
        """
        计算视频的所有分割点

        Args:
            video_path: 视频文件路径
            target_segment_duration: 目标片段时长（秒），默认30分钟
            search_range: 搜索范围（秒）
            progress_callback: 进度回调函数 (message, progress)

        Returns:
            分割时间点列表（秒）
        """
        # 获取视频时长
        total_duration = self.get_video_duration(video_path)

        # 如果视频时长小于目标时长的1.5倍，不需要分割
        if total_duration < target_segment_duration * 1.5:
            return []

        # 计算需要分割成几段
        num_segments = round(total_duration / target_segment_duration)
        if num_segments < 2:
            return []

        # 计算每个分割点的目标时间
        segment_duration = total_duration / num_segments
        target_times = [
            segment_duration * (i + 1)
            for i in range(num_segments - 1)
        ]

        # 在每个目标时间点附近寻找静音分割点
        split_points = []
        for i, target_time in enumerate(target_times):
            if progress_callback:
                progress = (i + 1) / len(target_times)
                progress_callback(f"正在分析分割点 {i + 1}/{len(target_times)}", progress)

            split_point = self.find_silence_near_target(
                video_path,
                target_time,
                search_range
            )

            if split_point is not None:
                split_points.append(split_point)
            else:
                # 如果没找到静音区域，使用目标时间点
                split_points.append(target_time)

        return split_points
