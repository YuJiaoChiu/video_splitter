"""
配置管理模块
"""
import os
import json
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Config:
    """程序配置"""
    # 默认目标片段时长（分钟）
    target_duration_minutes: int = 30

    # 搜索静音的范围（秒）- 在目标时间点前后各搜索这么长时间
    search_range_seconds: int = 600

    # 最小静音持续时间（秒）
    min_silence_duration: float = 1.0

    # 静音阈值（dBFS）- 低于此值视为静音
    silence_threshold_db: int = -40

    # 输出模式: "new" 或 "overwrite"
    output_mode: str = "new"

    # 输出目录（仅在 output_mode="new" 时使用）
    output_directory: Optional[str] = None

    # 支持的视频格式
    video_extensions: tuple = (".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v")

    # 配置文件路径
    _config_file: str = ""

    def __post_init__(self):
        self._config_file = os.path.join(
            os.path.expanduser("~"), ".video_splitter_config.json"
        )

    def save(self):
        """保存配置到文件"""
        data = asdict(self)
        # 移除私有属性和不可序列化的属性
        data.pop("_config_file", None)
        data["video_extensions"] = list(data["video_extensions"])

        with open(self._config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self):
        """从文件加载配置"""
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for key, value in data.items():
                    if hasattr(self, key) and not key.startswith("_"):
                        if key == "video_extensions":
                            value = tuple(value)
                        setattr(self, key, value)
            except (json.JSONDecodeError, IOError):
                pass  # 使用默认值

    @property
    def target_duration_seconds(self) -> int:
        """获取目标片段时长（秒）"""
        return self.target_duration_minutes * 60
