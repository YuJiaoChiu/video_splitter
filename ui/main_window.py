"""
主窗口模块
"""
import os
from typing import Optional, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
    QRadioButton, QButtonGroup, QFileDialog, QMessageBox,
    QSizePolicy, QSpacerItem, QApplication, QScrollArea,
    QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.styles import Styles
from ui.widgets import DropZone, FileListWidget, ProgressCard
from core.video_splitter import VideoSplitter, VideoInfo
from core.file_manager import FileManager, OutputMode, VideoFile
from utils.config import Config


class ProcessingThread(QThread):
    """处理线程"""

    # 信号
    progress = pyqtSignal(int, str, str)  # (progress, status, filename)
    file_completed = pyqtSignal(int, str)  # (index, status)
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
        """取消处理"""
        self._is_cancelled = True

    def run(self):
        """运行处理"""
        try:
            # 如果是新建模式，先复制非视频文件
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
                    # 获取视频信息
                    video_info = self.splitter.get_video_info(video_file.path)

                    # 确定输出目录
                    out_dir = self.file_manager.get_output_path(
                        video_file,
                        self.source_dir,
                        self.output_dir,
                        self.output_mode
                    )
                    self.file_manager.ensure_directory(out_dir)

                    # 检查是否需要分割
                    if not self.splitter.needs_splitting(video_info):
                        # 不需要分割，直接复制（如果是新建模式）
                        if self.output_mode == OutputMode.NEW:
                            import shutil
                            dst_path = os.path.join(out_dir, video_file.filename)
                            shutil.copy2(video_file.path, dst_path)
                        self.file_completed.emit(i, "skip")
                        continue

                    # 执行分割
                    def progress_callback(msg, p):
                        file_progress = int(base_progress + (p * 100 / total_files))
                        self.progress.emit(file_progress, msg, filename)

                    output_files = self.splitter.split_video(
                        video_file.path,
                        out_dir,
                        progress_callback
                    )

                    # 如果是覆盖模式，删除原文件
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
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.config = Config()
        self.config.load()
        self.splitter = None
        self.file_manager = FileManager()
        self.video_files: List[VideoFile] = []
        self.source_dir = ""
        self.processing_thread: Optional[ProcessingThread] = None

        self._setup_ui()
        self._connect_signals()
        self._update_splitter()

    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("视频智能分割器")
        self.setMinimumSize(700, 600)
        self.resize(800, 700)

        # 设置样式
        self.setStyleSheet(Styles.get_main_stylesheet())

        # 中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 标题行
        title_layout = QHBoxLayout()
        title_label = QLabel("视频智能分割器")
        title_label.setProperty("class", "title")
        subtitle_label = QLabel("根据音频静音自动分割视频")
        subtitle_label.setProperty("class", "subtitle")
        title_layout.addWidget(title_label)
        title_layout.addSpacing(12)
        title_layout.addWidget(subtitle_label)
        title_layout.addStretch()
        main_layout.addLayout(title_layout)

        # 拖拽区域
        self.drop_zone = DropZone()
        main_layout.addWidget(self.drop_zone)

        # ========== 设置区域（使用网格布局使其更紧凑）==========
        settings_group = QGroupBox("设置")
        settings_layout = QGridLayout(settings_group)
        settings_layout.setSpacing(10)
        settings_layout.setContentsMargins(12, 16, 12, 12)

        # 第一行：输出模式
        self.mode_group = QButtonGroup(self)
        self.new_mode_radio = QRadioButton("重新生成到新目录")
        self.overwrite_mode_radio = QRadioButton("覆盖源文件")
        self.mode_group.addButton(self.new_mode_radio, 0)
        self.mode_group.addButton(self.overwrite_mode_radio, 1)
        self.new_mode_radio.setChecked(True)

        settings_layout.addWidget(QLabel("输出模式:"), 0, 0)
        mode_widget = QWidget()
        mode_hlayout = QHBoxLayout(mode_widget)
        mode_hlayout.setContentsMargins(0, 0, 0, 0)
        mode_hlayout.setSpacing(20)
        mode_hlayout.addWidget(self.new_mode_radio)
        mode_hlayout.addWidget(self.overwrite_mode_radio)
        mode_hlayout.addStretch()
        settings_layout.addWidget(mode_widget, 0, 1, 1, 3)

        # 第二行：输出目录
        settings_layout.addWidget(QLabel("输出目录:"), 1, 0)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("选择输出目录...")
        settings_layout.addWidget(self.output_dir_edit, 1, 1, 1, 2)
        self.browse_btn = QPushButton("选择...")
        self.browse_btn.setFixedWidth(70)
        settings_layout.addWidget(self.browse_btn, 1, 3)

        # 第三行：分割参数
        settings_layout.addWidget(QLabel("目标片段:"), 2, 0)
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(5, 120)
        self.duration_spin.setValue(self.config.target_duration_minutes)
        self.duration_spin.setSuffix(" 分钟")
        self.duration_spin.setFixedWidth(90)
        settings_layout.addWidget(self.duration_spin, 2, 1)

        settings_layout.addWidget(QLabel("搜索范围:"), 2, 2)
        self.search_spin = QSpinBox()
        self.search_spin.setRange(60, 1200)
        self.search_spin.setValue(self.config.search_range_seconds)
        self.search_spin.setSuffix(" 秒")
        self.search_spin.setFixedWidth(90)
        settings_layout.addWidget(self.search_spin, 2, 3)

        # 第四行：静音参数
        settings_layout.addWidget(QLabel("最小静音:"), 3, 0)
        self.silence_spin = QDoubleSpinBox()
        self.silence_spin.setRange(0.1, 5.0)
        self.silence_spin.setValue(self.config.min_silence_duration)
        self.silence_spin.setSuffix(" 秒")
        self.silence_spin.setSingleStep(0.1)
        self.silence_spin.setFixedWidth(90)
        settings_layout.addWidget(self.silence_spin, 3, 1)

        settings_layout.addWidget(QLabel("长静音阈值:"), 3, 2)
        self.long_silence_spin = QSpinBox()
        self.long_silence_spin.setRange(60, 3600)
        self.long_silence_spin.setValue(self.config.long_silence_threshold)
        self.long_silence_spin.setSuffix(" 秒")
        self.long_silence_spin.setFixedWidth(90)
        settings_layout.addWidget(self.long_silence_spin, 3, 3)

        # 设置列拉伸
        settings_layout.setColumnStretch(1, 1)
        settings_layout.setColumnStretch(3, 1)

        main_layout.addWidget(settings_group)

        # ========== 文件列表 ==========
        file_group = QGroupBox("待处理文件")
        file_layout = QVBoxLayout(file_group)
        file_layout.setContentsMargins(8, 12, 8, 8)

        self.file_list = FileListWidget()
        file_layout.addWidget(self.file_list)

        main_layout.addWidget(file_group, 1)  # 使文件列表可扩展

        # ========== 进度区域 ==========
        self.progress_card = ProgressCard()
        main_layout.addWidget(self.progress_card)

        # ========== 按钮区域 ==========
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.save_settings_btn = QPushButton("保存设置")
        self.save_settings_btn.setFixedHeight(36)
        self.save_settings_btn.setFixedWidth(90)

        self.clear_btn = QPushButton("清空列表")
        self.clear_btn.setFixedHeight(36)
        self.clear_btn.setFixedWidth(90)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setProperty("class", "danger")
        self.stop_btn.setFixedHeight(36)
        self.stop_btn.setFixedWidth(80)
        self.stop_btn.setEnabled(False)

        self.start_btn = QPushButton("开始处理")
        self.start_btn.setProperty("class", "primary")
        self.start_btn.setFixedHeight(36)
        self.start_btn.setFixedWidth(100)
        self.start_btn.setEnabled(False)

        btn_layout.addWidget(self.save_settings_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.start_btn)

        main_layout.addLayout(btn_layout)

    def _connect_signals(self):
        """连接信号"""
        self.drop_zone.folder_dropped.connect(self._on_folder_selected)
        self.drop_zone.clicked.connect(self._browse_source_folder)
        self.browse_btn.clicked.connect(self._browse_output_folder)
        self.new_mode_radio.toggled.connect(self._on_mode_changed)
        self.start_btn.clicked.connect(self._start_processing)
        self.stop_btn.clicked.connect(self._stop_processing)
        self.clear_btn.clicked.connect(self._clear_list)
        self.save_settings_btn.clicked.connect(self._save_settings)

        # 设置变更时更新分割器
        self.duration_spin.valueChanged.connect(self._update_splitter)
        self.search_spin.valueChanged.connect(self._update_splitter)
        self.silence_spin.valueChanged.connect(self._update_splitter)
        self.long_silence_spin.valueChanged.connect(self._update_splitter)

    def _update_splitter(self):
        """更新分割器配置"""
        self.splitter = VideoSplitter(
            target_duration_seconds=self.duration_spin.value() * 60,
            search_range_seconds=self.search_spin.value(),
            silence_threshold_db=self.config.silence_threshold_db,
            min_silence_duration=self.silence_spin.value(),
            long_silence_threshold=self.long_silence_spin.value()
        )
        # 更新文件列表显示
        self._refresh_file_list()

    def _on_mode_changed(self, checked: bool):
        """输出模式变更"""
        self.output_dir_edit.setEnabled(checked)
        self.browse_btn.setEnabled(checked)

    def _save_settings(self):
        """保存当前设置"""
        self.config.target_duration_minutes = self.duration_spin.value()
        self.config.search_range_seconds = self.search_spin.value()
        self.config.min_silence_duration = self.silence_spin.value()
        self.config.long_silence_threshold = self.long_silence_spin.value()
        self.config.save()
        QMessageBox.information(self, "保存成功", "设置已保存，下次启动将自动加载。")

    def _browse_source_folder(self):
        """浏览源文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择包含视频的文件夹",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self._on_folder_selected(folder)

    def _browse_output_folder(self):
        """浏览输出文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.output_dir_edit.setText(folder)

    def _on_folder_selected(self, folder: str):
        """文件夹被选择"""
        if not os.path.isdir(folder):
            QMessageBox.warning(self, "错误", "请选择一个有效的文件夹")
            return

        self.source_dir = folder
        self.drop_zone.set_path(folder)

        # 设置默认输出目录
        if not self.output_dir_edit.text():
            parent = os.path.dirname(folder)
            folder_name = os.path.basename(folder)
            default_output = os.path.join(parent, f"{folder_name}_split")
            self.output_dir_edit.setText(default_output)

        # 扫描视频文件
        self.progress_card.set_progress(0, "正在扫描文件...")
        QApplication.processEvents()

        self.video_files = self.file_manager.scan_directory(folder)
        self._refresh_file_list()

        self.progress_card.reset()
        self.start_btn.setEnabled(len(self.video_files) > 0)

    def _refresh_file_list(self):
        """刷新文件列表"""
        self.file_list.clear_all()

        if not self.splitter:
            return

        for vf in self.video_files:
            try:
                video_info = self.splitter.get_video_info(vf.path)
                needs_split = self.splitter.needs_splitting(video_info)
                segments = self.splitter.calculate_segments(video_info)

                self.file_list.add_video_item(
                    vf.filename,
                    video_info.duration_str,
                    "pending",
                    needs_split,
                    segments
                )
            except Exception as e:
                self.file_list.add_video_item(
                    vf.filename,
                    "无法读取",
                    "error",
                    False,
                    0
                )

    def _clear_list(self):
        """清空列表"""
        self.video_files = []
        self.source_dir = ""
        self.file_list.clear_all()
        self.drop_zone.set_path("")
        self.progress_card.reset()
        self.start_btn.setEnabled(False)

    def _start_processing(self):
        """开始处理"""
        if not self.video_files:
            return

        # 检查输出目录
        output_mode = OutputMode.NEW if self.new_mode_radio.isChecked() else OutputMode.OVERWRITE

        if output_mode == OutputMode.NEW:
            output_dir = self.output_dir_edit.text()
            if not output_dir:
                QMessageBox.warning(self, "错误", "请指定输出目录")
                return
            # 确保输出目录是唯一的
            output_dir = self.file_manager.get_unique_output_dir(output_dir)
            self.output_dir_edit.setText(output_dir)
        else:
            output_dir = self.source_dir
            # 确认覆盖
            reply = QMessageBox.question(
                self,
                "确认覆盖",
                "覆盖模式将删除原始视频文件，是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # 保存配置
        self.config.target_duration_minutes = self.duration_spin.value()
        self.config.search_range_seconds = self.search_spin.value()
        self.config.min_silence_duration = self.silence_spin.value()
        self.config.long_silence_threshold = self.long_silence_spin.value()
        self.config.save()

        # 禁用UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.drop_zone.setEnabled(False)

        # 启动处理线程
        self.processing_thread = ProcessingThread(
            self.video_files,
            self.source_dir,
            output_dir,
            output_mode,
            self.splitter,
            self.file_manager
        )
        self.processing_thread.progress.connect(self._on_progress)
        self.processing_thread.file_completed.connect(self._on_file_completed)
        self.processing_thread.all_completed.connect(self._on_all_completed)
        self.processing_thread.error.connect(self._on_error)
        self.processing_thread.start()

    def _stop_processing(self):
        """停止处理"""
        if self.processing_thread:
            self.processing_thread.cancel()
            self.processing_thread.wait()
            self.processing_thread = None

        self._reset_ui()
        self.progress_card.set_progress(0, "已停止")

    def _on_progress(self, value: int, status: str, filename: str):
        """进度更新"""
        self.progress_card.set_progress(value, status, filename)

    def _on_file_completed(self, index: int, status: str):
        """文件处理完成"""
        self.file_list.update_item_status(index, status)

    def _on_all_completed(self):
        """全部完成"""
        self._reset_ui()
        QMessageBox.information(self, "完成", "所有视频处理完成！")

    def _on_error(self, message: str):
        """错误处理"""
        self._reset_ui()
        QMessageBox.critical(self, "错误", f"处理过程中出错:\n{message}")

    def _reset_ui(self):
        """重置UI状态"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.drop_zone.setEnabled(True)

    def closeEvent(self, event):
        """关闭事件"""
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "确认退出",
                "视频正在处理中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self.processing_thread.cancel()
            self.processing_thread.wait()

        event.accept()
