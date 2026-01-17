"""
样式表模块 - 现代风格
"""


class Styles:
    """应用程序样式"""

    # 主色调
    PRIMARY_COLOR = "#2563EB"  # 蓝色
    PRIMARY_HOVER = "#1D4ED8"
    PRIMARY_LIGHT = "#DBEAFE"
    SUCCESS_COLOR = "#10B981"  # 绿色
    WARNING_COLOR = "#F59E0B"  # 橙色
    DANGER_COLOR = "#EF4444"   # 红色
    GRAY_100 = "#F3F4F6"
    GRAY_200 = "#E5E7EB"
    GRAY_300 = "#D1D5DB"
    GRAY_400 = "#9CA3AF"
    GRAY_500 = "#6B7280"
    GRAY_600 = "#4B5563"
    GRAY_700 = "#374151"
    GRAY_800 = "#1F2937"
    WHITE = "#FFFFFF"

    # 兼容性别名
    TEXT_PRIMARY = GRAY_800
    TEXT_SECONDARY = GRAY_500

    @classmethod
    def get_main_stylesheet(cls) -> str:
        """获取主样式表"""
        return f"""
            /* 全局样式 */
            QWidget {{
                font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
                font-size: 14px;
                color: {cls.GRAY_800};
            }}

            QMainWindow {{
                background-color: {cls.GRAY_100};
            }}

            /* 标签 */
            QLabel {{
                color: {cls.GRAY_700};
            }}

            QLabel[class="title"] {{
                font-size: 22px;
                font-weight: bold;
                color: {cls.GRAY_800};
            }}

            QLabel[class="subtitle"] {{
                font-size: 14px;
                color: {cls.GRAY_500};
            }}

            /* 按钮 */
            QPushButton {{
                background-color: {cls.WHITE};
                border: 1px solid {cls.GRAY_300};
                border-radius: 8px;
                padding: 8px 20px;
                color: {cls.GRAY_700};
                font-weight: 500;
                min-height: 36px;
            }}

            QPushButton:hover {{
                background-color: {cls.GRAY_100};
                border-color: {cls.GRAY_400};
            }}

            QPushButton:pressed {{
                background-color: {cls.GRAY_200};
            }}

            QPushButton:disabled {{
                background-color: {cls.GRAY_100};
                color: {cls.GRAY_400};
                border-color: {cls.GRAY_200};
            }}

            QPushButton[class="primary"] {{
                background-color: {cls.PRIMARY_COLOR};
                border: none;
                color: {cls.WHITE};
            }}

            QPushButton[class="primary"]:hover {{
                background-color: {cls.PRIMARY_HOVER};
            }}

            QPushButton[class="primary"]:disabled {{
                background-color: {cls.GRAY_300};
            }}

            QPushButton[class="danger"] {{
                background-color: {cls.DANGER_COLOR};
                border: none;
                color: {cls.WHITE};
            }}

            QPushButton[class="danger"]:hover {{
                background-color: #DC2626;
            }}

            /* 输入框 */
            QLineEdit {{
                background-color: {cls.WHITE};
                border: 1px solid {cls.GRAY_300};
                border-radius: 8px;
                padding: 8px 12px;
                color: {cls.GRAY_800};
                min-height: 20px;
            }}

            QLineEdit:focus {{
                border-color: {cls.PRIMARY_COLOR};
                outline: none;
            }}

            QLineEdit:disabled {{
                background-color: {cls.GRAY_100};
                color: {cls.GRAY_400};
            }}

            /* 数字输入框 */
            QSpinBox, QDoubleSpinBox {{
                background-color: {cls.WHITE};
                border: 1px solid {cls.GRAY_300};
                border-radius: 8px;
                padding: 6px 10px;
                color: {cls.GRAY_800};
                min-height: 20px;
            }}

            QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {cls.PRIMARY_COLOR};
            }}

            QSpinBox::up-button, QSpinBox::down-button,
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                width: 20px;
                border: none;
                background-color: {cls.GRAY_100};
            }}

            QSpinBox::up-button:hover, QSpinBox::down-button:hover,
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
                background-color: {cls.GRAY_200};
            }}

            /* 单选按钮 */
            QRadioButton {{
                spacing: 8px;
                color: {cls.GRAY_700};
            }}

            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {cls.GRAY_300};
                background-color: {cls.WHITE};
            }}

            QRadioButton::indicator:checked {{
                border-color: {cls.PRIMARY_COLOR};
                background-color: {cls.PRIMARY_COLOR};
            }}

            QRadioButton::indicator:hover {{
                border-color: {cls.PRIMARY_COLOR};
            }}

            /* 进度条 */
            QProgressBar {{
                background-color: {cls.GRAY_200};
                border: none;
                border-radius: 6px;
                height: 14px;
                text-align: center;
                font-size: 11px;
                color: {cls.GRAY_600};
            }}

            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {cls.PRIMARY_COLOR}, stop:1 #60A5FA);
                border-radius: 6px;
            }}

            /* 列表 */
            QListWidget {{
                background-color: {cls.WHITE};
                border: 1px solid {cls.GRAY_200};
                border-radius: 12px;
                padding: 8px;
                outline: none;
            }}

            QListWidget::item {{
                background-color: {cls.WHITE};
                border-radius: 8px;
                padding: 10px;
                margin: 4px 0;
            }}

            QListWidget::item:hover {{
                background-color: {cls.GRAY_100};
            }}

            QListWidget::item:selected {{
                background-color: {cls.PRIMARY_LIGHT};
                color: {cls.PRIMARY_COLOR};
            }}

            /* 滚动条 */
            QScrollBar:vertical {{
                background-color: {cls.GRAY_100};
                width: 10px;
                border-radius: 5px;
                margin: 0;
            }}

            QScrollBar::handle:vertical {{
                background-color: {cls.GRAY_300};
                border-radius: 5px;
                min-height: 30px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {cls.GRAY_400};
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}

            QScrollBar:horizontal {{
                background-color: {cls.GRAY_100};
                height: 10px;
                border-radius: 5px;
            }}

            QScrollBar::handle:horizontal {{
                background-color: {cls.GRAY_300};
                border-radius: 5px;
                min-width: 30px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background-color: {cls.GRAY_400};
            }}

            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}

            /* 分组框 */
            QGroupBox {{
                background-color: {cls.WHITE};
                border: 1px solid {cls.GRAY_200};
                border-radius: 12px;
                margin-top: 16px;
                padding: 20px;
                padding-top: 30px;
                font-weight: bold;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 16px;
                padding: 0 8px;
                color: {cls.GRAY_700};
            }}

            /* 工具提示 */
            QToolTip {{
                background-color: {cls.GRAY_800};
                color: {cls.WHITE};
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
            }}
        """

    @classmethod
    def get_dropzone_style(cls, is_hover: bool = False) -> str:
        """获取拖拽区域样式"""
        border_color = cls.PRIMARY_COLOR if is_hover else cls.GRAY_300
        bg_color = cls.PRIMARY_LIGHT if is_hover else cls.WHITE

        return f"""
            background-color: {bg_color};
            border: 2px dashed {border_color};
            border-radius: 16px;
        """

    @classmethod
    def get_card_style(cls) -> str:
        """获取卡片样式"""
        return f"""
            background-color: {cls.WHITE};
            border: 1px solid {cls.GRAY_200};
            border-radius: 12px;
            padding: 16px;
        """

    @classmethod
    def get_status_style(cls, status: str) -> str:
        """获取状态样式"""
        colors = {
            "pending": cls.GRAY_500,
            "processing": cls.PRIMARY_COLOR,
            "completed": cls.SUCCESS_COLOR,
            "error": cls.DANGER_COLOR,
            "skip": cls.WARNING_COLOR
        }
        color = colors.get(status, cls.GRAY_500)
        return f"color: {color}; font-weight: 500;"
