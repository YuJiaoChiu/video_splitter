"""
自定义组件模块
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QProgressBar, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont

from .styles import Styles


class DropZone(QFrame):
    """拖拽区域组件"""

    folder_dropped = pyqtSignal(str)
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()
        self._update_style(False)

    def _setup_ui(self):
        """设置UI"""
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        # 图标
        self.icon_label = QLabel("📁")
        self.icon_label.setStyleSheet("font-size: 36px;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 提示文字
        self.hint_label = QLabel("拖拽文件夹到此处，或点击选择")
        self.hint_label.setStyleSheet(f"color: {Styles.GRAY_500}; font-size: 14px;")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 路径显示
        self.path_label = QLabel("")
        self.path_label.setStyleSheet(f"color: {Styles.GRAY_700}; font-size: 13px;")
        self.path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.path_label.setWordWrap(True)
        self.path_label.hide()

        layout.addWidget(self.icon_label)
        layout.addWidget(self.hint_label)
        layout.addWidget(self.path_label)

    def _update_style(self, is_hover: bool):
        """更新样式"""
        self.setStyleSheet(Styles.get_dropzone_style(is_hover))

    def set_path(self, path: str):
        """设置显示的路径"""
        if path:
            self.path_label.setText(path)
            self.path_label.show()
            self.hint_label.setText("点击更换文件夹")
        else:
            self.path_label.hide()
            self.hint_label.setText("拖拽文件夹到此处，或点击选择")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                event.acceptProposedAction()
                self._update_style(True)

    def dragLeaveEvent(self, event):
        self._update_style(False)

    def dropEvent(self, event: QDropEvent):
        self._update_style(False)
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self.folder_dropped.emit(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class FileListWidget(QListWidget):
    """文件列表组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setSpacing(2)
        # 确保滚动条始终可见
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def add_video_item(
        self,
        filename: str,
        duration: str,
        status: str = "pending",
        needs_split: bool = True,
        segments: int = 1
    ) -> QListWidgetItem:
        item = QListWidgetItem()
        widget = VideoItemWidget(filename, duration, status, needs_split, segments)
        # 设置固定的行高，确保显示完整
        from PyQt6.QtCore import QSize
        item.setSizeHint(QSize(0, 60))
        self.addItem(item)
        self.setItemWidget(item, widget)
        return item

    def update_item_status(self, row: int, status: str, message: str = ""):
        item = self.item(row)
        if item:
            widget = self.itemWidget(item)
            if isinstance(widget, VideoItemWidget):
                widget.set_status(status, message)

    def clear_all(self):
        self.clear()


class VideoItemWidget(QWidget):
    """视频项组件"""

    def __init__(
        self,
        filename: str,
        duration: str,
        status: str = "pending",
        needs_split: bool = True,
        segments: int = 1,
        parent=None
    ):
        super().__init__(parent)
        self.filename = filename
        self.duration = duration
        self.needs_split = needs_split
        self.segments = segments
        self._setup_ui()
        self.set_status(status)

    def _setup_ui(self):
        self.setFixedHeight(56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        # 图标
        icon_label = QLabel("🎬" if self.needs_split else "📄")
        icon_label.setStyleSheet("font-size: 24px;")
        icon_label.setFixedWidth(35)
        layout.addWidget(icon_label)

        # 文件信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.name_label = QLabel(self.filename)
        self.name_label.setStyleSheet(f"font-weight: 500; font-size: 13px; color: {Styles.GRAY_800};")

        detail_text = f"{self.duration}"
        if self.needs_split:
            detail_text += f" → 分割为 {self.segments} 段"
        else:
            detail_text += " (无需分割)"

        self.detail_label = QLabel(detail_text)
        self.detail_label.setStyleSheet(f"font-size: 13px; color: {Styles.GRAY_500};")

        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.detail_label)
        layout.addLayout(info_layout, 1)

        # 状态
        self.status_label = QLabel()
        self.status_label.setMinimumWidth(80)
        self.status_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.status_label)

    def set_status(self, status: str, message: str = ""):
        status_texts = {
            "pending": "待处理",
            "processing": "处理中...",
            "completed": "✓ 完成",
            "error": "✗ 错误",
            "skip": "跳过"
        }
        text = message if message else status_texts.get(status, status)
        self.status_label.setText(text)
        self.status_label.setStyleSheet(Styles.get_status_style(status))


class ProgressCard(QFrame):
    """进度卡片组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.setStyleSheet(Styles.get_card_style())

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 标题行
        title_layout = QHBoxLayout()

        self.title_label = QLabel("处理进度")
        self.title_label.setStyleSheet(f"font-weight: bold; color: {Styles.GRAY_800};")

        self.file_label = QLabel("")
        self.file_label.setStyleSheet(f"color: {Styles.GRAY_500};")

        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.file_label, 1)
        layout.addLayout(title_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 状态文字
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet(f"color: {Styles.GRAY_500}; font-size: 12px;")
        layout.addWidget(self.status_label)

    def set_progress(self, value: int, status: str = "", filename: str = ""):
        self.progress_bar.setValue(value)
        if status:
            self.status_label.setText(status)
        if filename:
            self.file_label.setText(filename)

    def reset(self):
        self.progress_bar.setValue(0)
        self.status_label.setText("就绪")
        self.file_label.setText("")


class SettingsCard(QFrame):
    """设置卡片组件"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(Styles.get_card_style())

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(12)

        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {Styles.GRAY_800};")
        self.main_layout.addWidget(title_label)

        # 内容区域
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(10)
        self.main_layout.addLayout(self.content_layout)

    def add_row(self, label: str, widget: QWidget):
        row_layout = QHBoxLayout()
        row_layout.setSpacing(12)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"color: {Styles.GRAY_600};")
        label_widget.setMinimumWidth(100)

        row_layout.addWidget(label_widget)
        row_layout.addWidget(widget, 1)

        self.content_layout.addLayout(row_layout)
