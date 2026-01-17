"""
视频分割模块 - 根据分割点分割视频
"""
import os
import subprocess
import re
from typing import List, Optional, Callable, Tuple
from dataclasses import dataclass

from .audio_analyzer import AudioAnalyzer


@dataclass
class VideoInfo:
    """视频信息"""
    path: str
    duration: float  # 秒
    width: int
    height: int
    fps: float
    codec: str
    audio_codec: str
    bitrate: Optional[int] = None

    @property
    def duration_str(self) -> str:
        """格式化的时长字符串 HH:MM:SS"""
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = int(self.duration % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def filename(self) -> str:
        return os.path.basename(self.path)

    @property
    def name_without_ext(self) -> str:
        return os.path.splitext(self.filename)[0]

    @property
    def extension(self) -> str:
        return os.path.splitext(self.filename)[1]


@dataclass
class SegmentInfo:
    """分割片段信息"""
    start: float
    end: float
    is_blank: bool  # 是否为空白片段
    index: int  # 片段序号

    @property
    def duration(self) -> float:
        return self.end - self.start

    @property
    def duration_str(self) -> str:
        """格式化的时长字符串 HH:MM:SS"""
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = int(self.duration % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"


class VideoSplitter:
    """视频分割器"""

    def __init__(
        self,
        target_duration_seconds: int = 1800,
        search_range_seconds: int = 60,
        silence_threshold_db: int = -40,
        min_silence_duration: float = 0.5,
        long_silence_threshold: int = 300
    ):
        """
        初始化视频分割器

        Args:
            target_duration_seconds: 目标片段时长（秒）
            search_range_seconds: 搜索静音的范围（秒）
            silence_threshold_db: 静音阈值（dBFS）
            min_silence_duration: 最小静音持续时间（秒）
            long_silence_threshold: 长静音阈值（秒），超过此时长单独导出
        """
        self.target_duration = target_duration_seconds
        self.search_range = search_range_seconds
        self.long_silence_threshold = long_silence_threshold
        self.audio_analyzer = AudioAnalyzer(
            silence_threshold_db=silence_threshold_db,
            min_silence_duration=min_silence_duration
        )

    def get_video_info(self, video_path: str) -> VideoInfo:
        """
        获取视频详细信息

        Args:
            video_path: 视频文件路径

        Returns:
            VideoInfo 对象
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,codec_name",
            "-show_entries", "format=duration,bit_rate",
            "-of", "json",
            video_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            import json
            data = json.loads(result.stdout)

            stream = data.get("streams", [{}])[0]
            format_info = data.get("format", {})

            # 解析帧率
            fps_str = stream.get("r_frame_rate", "30/1")
            if "/" in fps_str:
                num, den = map(int, fps_str.split("/"))
                fps = num / den if den != 0 else 30.0
            else:
                fps = float(fps_str)

            # 获取音频编码
            audio_cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=codec_name",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            audio_result = subprocess.run(audio_cmd, capture_output=True, text=True)
            audio_codec = audio_result.stdout.strip() or "aac"

            return VideoInfo(
                path=video_path,
                duration=float(format_info.get("duration", 0)),
                width=int(stream.get("width", 0)),
                height=int(stream.get("height", 0)),
                fps=fps,
                codec=stream.get("codec_name", "h264"),
                audio_codec=audio_codec,
                bitrate=int(format_info.get("bit_rate", 0)) if format_info.get("bit_rate") else None
            )
        except (subprocess.CalledProcessError, ValueError, KeyError) as e:
            raise RuntimeError(f"无法获取视频信息: {e}")

    def needs_splitting(self, video_info: VideoInfo) -> bool:
        """
        判断视频是否需要分割

        Args:
            video_info: 视频信息

        Returns:
            True 如果需要分割
        """
        # 如果视频时长小于目标时长的1.5倍，不需要分割
        return video_info.duration >= self.target_duration * 1.5

    def calculate_segments(self, video_info: VideoInfo) -> int:
        """
        计算视频将被分割成几段

        Args:
            video_info: 视频信息

        Returns:
            分割段数
        """
        if not self.needs_splitting(video_info):
            return 1
        return round(video_info.duration / self.target_duration)

    def split_video(
        self,
        video_path: str,
        output_dir: str,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> List[Tuple[str, bool]]:
        """
        分割视频

        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            progress_callback: 进度回调函数 (message, progress)

        Returns:
            输出文件信息列表 [(文件路径, 是否为空白片段), ...]
        """
        # 获取视频信息
        video_info = self.get_video_info(video_path)

        if not self.needs_splitting(video_info):
            if progress_callback:
                progress_callback("视频时长不足，无需分割", 1.0)
            return [(video_path, False)]

        # 计算分割点（使用长静音检测）
        if progress_callback:
            progress_callback("正在分析音频，寻找静音分割点...", 0.1)

        split_points, segment_info = self.audio_analyzer.calculate_split_points_with_long_silence(
            video_path,
            target_segment_duration=self.target_duration,
            search_range=self.search_range,
            long_silence_threshold=self.long_silence_threshold,
            progress_callback=lambda msg, p: progress_callback(msg, 0.1 + p * 0.2) if progress_callback else None
        )

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 分割视频
        output_files = []
        for i, (start_time, end_time, is_blank) in enumerate(segment_info):
            if progress_callback:
                segment_progress = (i / len(segment_info))
                status = "（空白）" if is_blank else ""
                progress_callback(
                    f"正在分割第 {i + 1}/{len(segment_info)} 段{status}...",
                    0.3 + segment_progress * 0.7
                )

            # 生成输出文件名
            if is_blank:
                output_filename = f"{video_info.name_without_ext}-{i + 1}-空白{video_info.extension}"
            else:
                output_filename = f"{video_info.name_without_ext}-{i + 1}{video_info.extension}"
            output_path = os.path.join(output_dir, output_filename)

            # 执行分割
            self._split_segment(
                video_path,
                output_path,
                start_time,
                end_time,
                video_info
            )
            output_files.append((output_path, is_blank))

        if progress_callback:
            progress_callback("分割完成", 1.0)

        return output_files

    def _split_segment(
        self,
        input_path: str,
        output_path: str,
        start_time: float,
        end_time: float,
        video_info: VideoInfo
    ):
        """
        分割视频的一个片段

        使用 stream copy 模式以保持原始质量和快速处理

        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            video_info: 视频信息
        """
        duration = end_time - start_time

        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-y",  # 覆盖输出文件
            "-ss", str(start_time),
            "-i", input_path,
            "-t", str(duration),
            "-c", "copy",  # 直接复制流，不重新编码
            "-avoid_negative_ts", "make_zero",
            output_path
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            # 如果 stream copy 失败，尝试重新编码
            cmd = [
                "ffmpeg",
                "-hide_banner",
                "-y",
                "-ss", str(start_time),
                "-i", input_path,
                "-t", str(duration),
                "-c:v", video_info.codec,
                "-c:a", video_info.audio_codec,
                output_path
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=True)

    def get_split_preview(self, video_info: VideoInfo) -> List[Tuple[str, str, bool]]:
        """
        获取分割预览信息

        Args:
            video_info: 视频信息

        Returns:
            [(片段名, 预计时长字符串, 是否为空白), ...]
        """
        if not self.needs_splitting(video_info):
            return [(video_info.filename, video_info.duration_str, False)]

        num_segments = self.calculate_segments(video_info)
        segment_duration = video_info.duration / num_segments

        preview = []
        for i in range(num_segments):
            name = f"{video_info.name_without_ext}-{i + 1}{video_info.extension}"
            # 最后一段可能时长不同
            if i == num_segments - 1:
                remaining = video_info.duration - (segment_duration * i)
                duration_str = self._format_duration(remaining)
            else:
                duration_str = self._format_duration(segment_duration)
            preview.append((name, f"~{duration_str}", False))

        return preview

    def _format_duration(self, seconds: float) -> str:
        """格式化时长"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
