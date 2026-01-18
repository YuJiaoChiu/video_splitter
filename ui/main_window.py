"""
主窗口模块 - 左右布局设计
"""
import os
from typing import Optional, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit,
    QRadioButton, QButtonGroup, QFileDialog, QMessageBox,
    QApplication, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.widgets import DropZone, FileListWidget, ProgressCard
from core.video_splitter import VideoSplitter, VideoInfo
from core.file_manager import FileManager, OutputMode, VideoFile
from utils.config import Config


class ProcessingThread(QThread):
    """处理线程"""

    progress = pyqtSignal(int, str, str)
    file_completed = pyqtSignal(int, str)
    all_completed = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self,
        video_files: List[VideoFile],
        source_dir: str,
        output_dir: str,
        output_mode: OutputMode,
        splitter: VideoSplitter,
        file_manager: FileManager
    ):
        super().__init__()
        self.video_files = video_files
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.output_mode = output_mode
        self.splitter = splitter
        self.file_manager = file_manager
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            if self.output_mode == OutputMode.NEW:
                self.progress.emit(0, "正在复制非视频文件...", "")
                self.file_manager.copy_non_video_files(
                    self.source_dir,
                    self.output_dir
                )

            total_files = len(self.video_files)

            for i, video_file in enumerate(self.video_files):
                if self._is_cancelled:
                    break

                filename = video_file.filename
                base_progress = int((i / total_files) * 100)

                self.progress.emit(base_progress, f"正在处理: {filename}", filename)

                try:
                    video_info = self.splitter.get_video_info(video_file.path)

                    out_dir = self.file_manager.get_output_path(
                        video_file,
                        self.source_dir,
                        self.output_dir,
                        self.output_mode
                    )
                    self.file_manager.ensure_directory(out_dir)

                    if not self.splitter.needs_splitting(video_info):
                        if self.output_mode == OutputMode.NEW:
                            import shutil
                            dst_path = os.path.join(out_dir, video_file.filename)
                            shutil.copy2(video_file.path, dst_path)
                        self.file_completed.emit(i, "skip")
                        continue

                    def progress_callback(msg, p):
                        file_progress = int(base_progress + (p * 100 / total_files))
                        self.progress.emit(file_progress, msg, filename)

                    output_files = self.splitter.split_video(
                        video_file.path,
                        out_dir,
                        progress_callback
                    )

                    if self.output_mode == OutputMode.OVERWRITE and output_files:
                        self.file_manager.delete_original_video(video_file.path)

                    self.file_completed.emit(i, "completed")

                except Exception as e:
                    self.file_completed.emit(i, f"error: {str(e)}")

            self.progress.emit(100, "处理完成", "")
            self.all_completed.emit()

        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """主窗口 - 左右布局"""

    def __init__(self):
        super().__init__()
        self.config = Config()
        self.config.load()
        self.file_manager = FileManager()
        self.video_files: List[VideoFile] = []
        self.source_dir = ""
        self.processing_thread: Optional[ProcessingThread] = None

        self._setup_ui()
        self._connect_signals()

    def _create_section_title(self, text: str) -> QLabel:
        """创建区块标题"""
        label = QLabel(text)
        label.setFixedHeight(40)
        label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 8px 0;
                border-bottom: 2px solid #3498db;
            }
        """)
        return label

    def _create_param_group(self, title: str, default_value: str, unit: str) -> tuple:
        """创建参数输入组"""
        container = QVBoxLayout()
        container.setSpacing(6)

        label = QLabel(title)
        label.setFixedHeight(24)
        label.setStyleSheet("font-size: 13px; color: #555;")
        container.addWidget(label)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        edit = QLineEdit()
        edit.setText(default_value)
        edit.setFixedWidth(80)
        edit.setFixedHeight(36)
        edit.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        input_row.addWidget(edit)

        unit_label = QLabel(unit)
        unit_label.setFixedHeight(36)
        unit_label.setStyleSheet("font-size: 13px; color: #666;")
        input_row.addWidget(unit_label)
        input_row.addStretch()

        container.addLayout(input_row)

        return container, edit

    def _setup_ui(self):
        """设置UI - 左右布局"""
        self.setWindowTitle("视频智能分割器")
        self.setMinimumSize(1100, 850)
        self.resize(1200, 900)

        # 主样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
            QPushButton {
                padding: 10px 20px;
                border: 1px solid #ddd;
                border-radius: 6px;
                background: white;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background: #f8f9fa;
                border-color: #ccc;
            }
            QPushButton[class="primary"] {
                background: #3498db;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton[class="primary"]:hover {
                background: #2980b9;
            }
            QPushButton[class="primary"]:disabled {
                background: #bdc3c7;
            }
            QPushButton[class="danger"] {
                background: #e74c3c;
                color: white;
                border: none;
            }
            QPushButton[class="danger"]:hover {
                background: #c0392b;
            }
            QRadioButton {
                font-size: 14px;
                spacing: 10px;
                min-height: 28px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 6px;
                background: white;
            }
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 6px;
                text-align: center;
                background: #ecf0f1;
                min-height: 24px;
            }
            QProgressBar::chunk {
                background: #3498db;
                border-radius: 5px;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 最外层垂直布局
        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(24, 24, 24, 24)
        outer_layout.setSpacing(20)

        # 标题区域
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)

        title_label = QLabel("视频智能分割器")
        title_label.setFixedHeight(36)
        title_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
        """)
        title_layout.addWidget(title_label)

        subtitle_label = QLabel("根据音频静音自动分割视频，智能寻找最佳分割点")
        subtitle_label.setFixedHeight(24)
        subtitle_label.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        title_layout.addWidget(subtitle_label)

        outer_layout.addWidget(title_widget)

        # ========== 主内容区：左右布局 ==========
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)

        # ===== 左侧面板：文件和进度 =====
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
            }
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(16)

        # 拖拽区域
        left_layout.addWidget(self._create_section_title("选择文件夹"))
        self.drop_zone = DropZone()
        self.drop_zone.setMinimumHeight(100)
        left_layout.addWidget(self.drop_zone)

        # 文件列表
        left_layout.addWidget(self._create_section_title("待处理文件"))
        self.file_list = FileListWidget()
        self.file_list.setMinimumHeight(250)
        left_layout.addWidget(self.file_list, 1)

        # 进度
        left_layout.addWidget(self._create_section_title("处理进度"))
        self.progress_card = ProgressCard()
        left_layout.addWidget(self.progress_card)

        content_layout.addWidget(left_panel, 1)

        # ===== 右侧面板：设置 =====
        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
            }
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(16)

        # ----- 输出设置 -----
        right_layout.addWidget(self._create_section_title("输出设置"))

        # 输出模式
        mode_container = QVBoxLayout()
        mode_container.setSpacing(10)

        self.mode_group = QButtonGroup(self)
        self.new_mode_radio = QRadioButton("生成到新目录（保留原文件）")
        self.overwrite_mode_radio = QRadioButton("覆盖源文件（删除原文件）")
        self.new_mode_radio.setChecked(True)
        self.mode_group.addButton(self.new_mode_radio, 0)
        self.mode_group.addButton(self.overwrite_mode_radio, 1)
        mode_container.addWidget(self.new_mode_radio)
        mode_container.addWidget(self.overwrite_mode_radio)
        right_layout.addLayout(mode_container)

        right_layout.addSpacing(10)

        # 输出目录
        dir_label = QLabel("输出目录")
        dir_label.setFixedHeight(24)
        dir_label.setStyleSheet("font-size: 13px; color: #555;")
        right_layout.addWidget(dir_label)

        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("选择或输入输出目录...")
        self.output_dir_edit.setFixedHeight(40)
        self.output_dir_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 6px;
                background: white;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        right_layout.addWidget(self.output_dir_edit)

        self.browse_btn = QPushButton("浏览选择目录...")
        self.browse_btn.setFixedHeight(40)
        right_layout.addWidget(self.browse_btn)

        right_layout.addSpacing(10)

        # ----- 分割参数 -----
        right_layout.addWidget(self._create_section_title("分割参数"))

        # 第一行参数
        row1 = QHBoxLayout()
        row1.setSpacing(30)

        duration_layout, self.duration_edit = self._create_param_group(
            "目标片段时长", str(self.config.target_duration_minutes), "分钟"
        )
        row1.addLayout(duration_layout)

        search_layout, self.search_edit = self._create_param_group(
            "静音搜索范围", str(self.config.search_range_seconds), "秒"
        )
        row1.addLayout(search_layout)

        row1.addStretch()
        right_layout.addLayout(row1)

        right_layout.addSpacing(8)

        # 第二行参数
        row2 = QHBoxLayout()
        row2.setSpacing(30)

        silence_layout, self.silence_edit = self._create_param_group(
            "最小静音时长", str(self.config.min_silence_duration), "秒"
        )
        row2.addLayout(silence_layout)

        long_silence_layout, self.long_silence_edit = self._create_param_group(
            "长静音阈值", str(self.config.long_silence_threshold), "秒"
        )
        row2.addLayout(long_silence_layout)

        row2.addStretch()
        right_layout.addLayout(row2)

        hint_label = QLabel("提示：超过长静音阈值的静音段将单独导出")
        hint_label.setFixedHeight(28)
        hint_label.setStyleSheet("font-size: 12px; color: #95a5a6;")
        right_layout.addWidget(hint_label)

        # 留白
        right_layout.addStretch()

        # ----- 操作按钮 -----
        right_layout.addWidget(self._create_section_title("操作"))

        self.save_settings_btn = QPushButton("保存设置")
        self.save_settings_btn.setFixedHeight(44)
        right_layout.addWidget(self.save_settings_btn)

        self.clear_btn = QPushButton("清空文件列表")
        self.clear_btn.setFixedHeight(44)
        right_layout.addWidget(self.clear_btn)

        right_layout.addSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setProperty("class", "danger")
        self.stop_btn.setFixedHeight(50)
        self.stop_btn.setEnabled(False)

        self.start_btn = QPushButton("开始处理")
        self.start_btn.setProperty("class", "primary")
        self.start_btn.setFixedHeight(50)
        self.start_btn.setEnabled(False)

        btn_row.addWidget(self.stop_btn)
        btn_row.addWidget(self.start_btn)
        right_layout.addLayout(btn_row)

        content_layout.addWidget(right_panel, 1)

        outer_layout.addLayout(content_layout, 1)

    def _connect_signals(self):
        self.drop_zone.folder_dropped.connect(self._on_folder_selected)
        self.drop_zone.clicked.connect(self._browse_source_folder)
        self.browse_btn.clicked.connect(self._browse_output_folder)
        self.new_mode_radio.toggled.connect(self._on_mode_changed)
        self.start_btn.clicked.connect(self._start_processing)
        self.stop_btn.clicked.connect(self._stop_processing)
        self.clear_btn.clicked.connect(self._clear_list)
        self.save_settings_btn.clicked.connect(self._save_settings)

    def _get_settings(self):
        """获取当前设置值"""
        try:
            duration = int(self.duration_edit.text())
        except ValueError:
            duration = 30

        try:
            search = int(self.search_edit.text())
        except ValueError:
            search = 60

        try:
            silence = float(self.silence_edit.text())
        except ValueError:
            silence = 0.5

        try:
            long_silence = int(self.long_silence_edit.text())
        except ValueError:
            long_silence = 300

        return duration, search, silence, long_silence

    def _create_splitter(self) -> VideoSplitter:
        """创建分割器"""
        duration, search, silence, long_silence = self._get_settings()
        return VideoSplitter(
            target_duration_seconds=duration * 60,
            search_range_seconds=search,
            silence_threshold_db=self.config.silence_threshold_db,
            min_silence_duration=silence,
            long_silence_threshold=long_silence
        )

    def _on_mode_changed(self, checked: bool):
        self.output_dir_edit.setEnabled(checked)
        self.browse_btn.setEnabled(checked)

    def _save_settings(self):
        duration, search, silence, long_silence = self._get_settings()
        self.config.target_duration_minutes = duration
        self.config.search_range_seconds = search
        self.config.min_silence_duration = silence
        self.config.long_silence_threshold = long_silence
        self.config.save()
        QMessageBox.information(self, "保存成功", "设置已保存，下次启动将自动加载。")

    def _browse_source_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "选择包含视频的文件夹", "", QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self._on_folder_selected(folder)

    def _browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "选择输出目录", "", QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.output_dir_edit.setText(folder)

    def _on_folder_selected(self, folder: str):
        if not os.path.isdir(folder):
            QMessageBox.warning(self, "错误", "请选择一个有效的文件夹")
            return

        self.source_dir = folder
        self.drop_zone.set_path(folder)

        if not self.output_dir_edit.text():
            parent = os.path.dirname(folder)
            folder_name = os.path.basename(folder)
            default_output = os.path.join(parent, f"{folder_name}_split")
            self.output_dir_edit.setText(default_output)

        # 只扫描文件，不获取视频信息
        self.video_files = self.file_manager.scan_directory(folder)

        # 简单显示文件列表
        self.file_list.clear_all()
        for vf in self.video_files:
            self.file_list.add_video_item(
                vf.filename,
                "",
                "pending",
                False,
                0
            )

        self.start_btn.setEnabled(len(self.video_files) > 0)

    def _clear_list(self):
        self.video_files = []
        self.source_dir = ""
        self.file_list.clear_all()
        self.drop_zone.set_path("")
        self.progress_card.reset()
        self.start_btn.setEnabled(False)

    def _start_processing(self):
        if not self.video_files:
            return

        output_mode = OutputMode.NEW if self.new_mode_radio.isChecked() else OutputMode.OVERWRITE

        if output_mode == OutputMode.NEW:
            output_dir = self.output_dir_edit.text()
            if not output_dir:
                QMessageBox.warning(self, "错误", "请指定输出目录")
                return
            output_dir = self.file_manager.get_unique_output_dir(output_dir)
            self.output_dir_edit.setText(output_dir)
        else:
            output_dir = self.source_dir
            reply = QMessageBox.question(
                self, "确认覆盖",
                "覆盖模式将删除原始视频文件，是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # 保存配置
        duration, search, silence, long_silence = self._get_settings()
        self.config.target_duration_minutes = duration
        self.config.search_range_seconds = search
        self.config.min_silence_duration = silence
        self.config.long_silence_threshold = long_silence
        self.config.save()

        # 创建分割器
        splitter = self._create_splitter()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.drop_zone.setEnabled(False)

        self.processing_thread = ProcessingThread(
            self.video_files, self.source_dir, output_dir,
            output_mode, splitter, self.file_manager
        )
        self.processing_thread.progress.connect(self._on_progress)
        self.processing_thread.file_completed.connect(self._on_file_completed)
        self.processing_thread.all_completed.connect(self._on_all_completed)
        self.processing_thread.error.connect(self._on_error)
        self.processing_thread.start()

    def _stop_processing(self):
        if self.processing_thread:
            self.processing_thread.cancel()
            self.processing_thread.wait()
            self.processing_thread = None

        self._reset_ui()
        self.progress_card.set_progress(0, "已停止")

    def _on_progress(self, value: int, status: str, filename: str):
        self.progress_card.set_progress(value, status, filename)

    def _on_file_completed(self, index: int, status: str):
        self.file_list.update_item_status(index, status)

    def _on_all_completed(self):
        self._reset_ui()
        QMessageBox.information(self, "完成", "所有视频处理完成！")

    def _on_error(self, message: str):
        self._reset_ui()
        QMessageBox.critical(self, "错误", f"处理过程中出错:\n{message}")

    def _reset_ui(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.drop_zone.setEnabled(True)

    def closeEvent(self, event):
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self, "确认退出", "视频正在处理中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self.processing_thread.cancel()
            self.processing_thread.wait()

        event.accept()
