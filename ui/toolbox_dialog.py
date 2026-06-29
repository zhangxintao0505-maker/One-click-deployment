"""工具箱对话框 - iOS 极简风 + Claude 暖色调"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QWidget, QFrame,
    QGridLayout, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QFont, QColor, QMouseEvent


# ═══════════════════════════════════════════════════════════════
# 配色方案
# ═══════════════════════════════════════════════════════════════
COLORS = {
    "bg": "#FBF9F6",           # 主背景 - 暖白/纸张色
    "card": "#FFFFFF",         # 卡片背景 - 纯白
    "card_border": "#EBE7E0",  # 卡片边框 - 极浅暖灰
    "title": "#222220",        # 标题文字 - 深炭黑
    "desc": "#8C867E",         # 描述文字 - 中灰
    "nav_active": "#222220",   # 导航选中
    "nav_inactive": "#8C867E", # 导航未选中
    "nav_hover": "#F5F3F0",    # 导航悬停
    "divider": "#EBE7E0",      # 分割线
    "icon": "#222220",         # 图标颜色 - 深炭黑
}


class WindowTitleBar(QWidget):
    """自定义标题栏 - Windows 按钮 + iOS 风格"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_dialog = parent
        self.setFixedHeight(48)
        self.setStyleSheet(f"""
            background-color: {COLORS['card']};
            border-top-left-radius: 16px;
            border-top-right-radius: 16px;
        """)
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 0, 0)
        layout.setSpacing(0)

        # 标题
        title_label = QLabel("🧰  工具箱")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 15px;
                font-weight: 600;
                color: {COLORS["title"]};
                background: transparent;
            }}
        """)
        layout.addWidget(title_label)
        layout.addStretch()

        # Windows 风格按钮（右侧）
        btn_style_base = """
            QPushButton {
                border: none;
                border-radius: 0px;
                font-size: 10px;
                font-weight: bold;
            }
        """

        # 最小化按钮
        self.btn_minimize = QPushButton("─")
        self.btn_minimize.setFixedSize(46, 32)
        self.btn_minimize.setStyleSheet(f"""
            {btn_style_base}
            QPushButton {{
                background-color: transparent;
                color: {COLORS["title"]};
                border-top-right-radius: 0px;
            }}
            QPushButton:hover {{
                background-color: #E5E5E5;
            }}
        """)
        self.btn_minimize.clicked.connect(self._on_minimize)
        layout.addWidget(self.btn_minimize)

        # 最大化按钮
        self.btn_maximize = QPushButton("□")
        self.btn_maximize.setFixedSize(46, 32)
        self.btn_maximize.setStyleSheet(f"""
            {btn_style_base}
            QPushButton {{
                background-color: transparent;
                color: {COLORS["title"]};
            }}
            QPushButton:hover {{
                background-color: #E5E5E5;
            }}
        """)
        self.btn_maximize.clicked.connect(self._on_maximize)
        layout.addWidget(self.btn_maximize)

        # 关闭按钮
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(46, 32)
        self.btn_close.setStyleSheet(f"""
            {btn_style_base}
            QPushButton {{
                background-color: transparent;
                color: {COLORS["title"]};
                border-top-right-radius: 16px;
            }}
            QPushButton:hover {{
                background-color: #E81123;
                color: white;
            }}
        """)
        self.btn_close.clicked.connect(self._on_close)
        layout.addWidget(self.btn_close)

        # 窗口状态
        self._is_maximized = False

    def _on_close(self):
        if self.parent_dialog:
            self.parent_dialog.close()

    def _on_minimize(self):
        if self.parent_dialog:
            self.parent_dialog.showMinimized()

    def _on_maximize(self):
        if self.parent_dialog:
            if self._is_maximized:
                self.parent_dialog.showNormal()
                self._is_maximized = False
            else:
                self.parent_dialog.showMaximized()
                self._is_maximized = True

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.parent_dialog:
            self._drag_pos = event.globalPosition().toPoint() - self.parent_dialog.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos is not None and self.parent_dialog:
            self.parent_dialog.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self._on_maximize()


class ToolCard(QFrame):
    """工具卡片组件 - iOS 极简风"""
    clicked = Signal(str)

    def __init__(self, name, title, description, icon_text="", parent=None):
        super().__init__(parent)
        self.tool_name = name
        self.icon_text = icon_text
        self._title = title
        self._description = description
        self._init_ui()

    def _init_ui(self):
        self.setFixedSize(280, 160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            ToolCard {{
                background-color: {COLORS["card"]};
                border: 1px solid {COLORS["card_border"]};
                border-radius: 16px;
            }}
            ToolCard:hover {{
                border-color: #D4CFC7;
                background-color: #FEFEFE;
            }}
        """)

        # 阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 12))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # 图标 - 简洁文字图标，无背景色块
        icon_label = QLabel(self.icon_text)
        icon_label.setFixedSize(32, 32)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                color: {COLORS["icon"]};
                border: none;
                background: transparent;
            }}
        """)
        layout.addWidget(icon_label)

        # 标题
        title = QLabel(self._title)
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 15px;
                font-weight: 600;
                color: {COLORS["title"]};
                border: none;
                background: transparent;
                letter-spacing: 0.2px;
            }}
        """)
        layout.addWidget(title)

        # 描述
        desc = QLabel(self._description)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: {COLORS["desc"]};
                border: none;
                background: transparent;
                line-height: 1.5;
            }}
        """)
        layout.addWidget(desc)

        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.tool_name)
        super().mousePressEvent(event)


class ToolboxDialog(QDialog):
    """工具箱对话框 - iOS 极简风 + Claude 暖色调"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # 无边框窗口 - Windows 兼容
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("工具箱")
        self.setMinimumSize(1000, 650)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)  # 留出阴影空间
        layout.setSpacing(0)

        # 主容器 - 带圆角和阴影
        main_widget = QWidget()
        main_widget.setStyleSheet(f"""
            background-color: {COLORS['bg']};
            border-radius: 16px;
            border: 1px solid {COLORS['divider']};
        """)

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 25))
        main_widget.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 自定义标题栏
        self._title_bar = WindowTitleBar(self)
        main_layout.addWidget(self._title_bar)

        # 内容区域
        content_container = QWidget()
        content_container.setStyleSheet("background: transparent;")
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # ═══════════════════════════════════════════════════════════
        # 左侧导航栏
        # ═══════════════════════════════════════════════════════════
        nav_widget = QWidget()
        nav_widget.setFixedWidth(200)
        nav_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS["card"]};
                border-right: 1px solid {COLORS["divider"]};
                border-top-left-radius: 16px;
                border-bottom-left-radius: 16px;
            }}
        """)
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(16, 24, 16, 24)
        nav_layout.setSpacing(4)

        # 导航项
        nav_items = [
            ("deploy", "🚀", "部署工具"),
            ("database", "🗄️", "数据库"),
            ("network", "🌐", "网络工具"),
            ("format", "🔄", "格式转换"),
            ("system", "⚙️", "系统工具"),
        ]

        self.nav_buttons = {}
        for name, icon, text in nav_items:
            btn_container = QWidget()
            btn_container.setObjectName(f"nav_{name}")
            btn_container.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_container.setStyleSheet(f"""
                QWidget#nav_{name} {{
                    background-color: transparent;
                    border-radius: 10px;
                }}
                QWidget#nav_{name}:hover {{
                    background-color: {COLORS["nav_hover"]};
                }}
            """)

            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(12, 10, 12, 10)
            btn_layout.setSpacing(10)

            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 16px; border: none; background: transparent;")
            btn_layout.addWidget(icon_label)

            text_label = QLabel(text)
            text_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 14px;
                    font-weight: 500;
                    color: {COLORS["nav_inactive"]};
                    border: none;
                    background: transparent;
                }}
            """)
            btn_layout.addWidget(text_label)
            btn_layout.addStretch()

            btn_container.mousePressEvent = lambda event, n=name: self._on_nav_clicked(n)
            self.nav_buttons[name] = {"container": btn_container, "text": text_label}
            nav_layout.addWidget(btn_container)

        nav_layout.addStretch()

        # 版本
        version_label = QLabel("v1.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {COLORS["desc"]};
                border: none;
                background: transparent;
                padding: 8px;
            }}
        """)
        nav_layout.addWidget(version_label)

        content_layout.addWidget(nav_widget)

        # ═══════════════════════════════════════════════════════════
        # 右侧内容区
        # ═══════════════════════════════════════════════════════════
        content_widget = QWidget()
        content_widget.setStyleSheet(f"""
            background-color: {COLORS['bg']};
            border-top-right-radius: 16px;
            border-bottom-right-radius: 16px;
        """)
        content_layout_right = QVBoxLayout(content_widget)
        content_layout_right.setContentsMargins(40, 36, 40, 24)
        content_layout_right.setSpacing(20)

        # 标题区域
        header_widget = QWidget()
        header_widget.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        self.section_title = QLabel("部署工具")
        self.section_title.setStyleSheet(f"""
            QLabel {{
                font-size: 26px;
                font-weight: 600;
                color: {COLORS["title"]};
                border: none;
                background: transparent;
            }}
        """)
        header_layout.addWidget(self.section_title)

        self.section_desc = QLabel("服务器部署与管理相关工具")
        self.section_desc.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {COLORS["desc"]};
                border: none;
                background: transparent;
            }}
        """)
        header_layout.addWidget(self.section_desc)

        content_layout_right.addWidget(header_widget)

        # 极淡分割线
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"""
            background-color: {COLORS["divider"]};
            border: none;
        """)
        content_layout_right.addWidget(divider)

        # 工具卡片区域（滚动）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                width: 6px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background: #D4CFC7;
                border-radius: 3px;
                min-height: 40px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #B8B2A8;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(20)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll_area.setWidget(self.cards_container)
        content_layout_right.addWidget(scroll_area)

        content_layout.addWidget(content_widget)

        main_layout.addWidget(content_container)

        layout.addWidget(main_widget)

        layout.addWidget(main_widget)

        # 初始化
        self._init_tools()
        self._on_nav_clicked("deploy")

    def paintEvent(self, event):
        """绘制圆角背景"""
        from PySide6.QtGui import QPainter, QBrush, QColor, QPainterPath
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制圆角矩形背景
        path = QPainterPath()
        rect = self.rect().adjusted(10, 10, -10, -10)
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 16, 16)

        painter.fillPath(path, QBrush(QColor(COLORS['bg'])))
        painter.strokePath(path, QPen(QColor(COLORS['divider']), 1))

        painter.end()

    def changeEvent(self, event):
        """窗口状态变化事件"""
        super().changeEvent(event)
        if hasattr(self, '_title_bar'):
            if self.isMaximized():
                self._title_bar._is_maximized = True
                self._title_bar.btn_maximize.setText("❐")
            else:
                self._title_bar._is_maximized = False
                self._title_bar.btn_maximize.setText("□")

    def _init_tools(self):
        """初始化工具数据"""
        self.tools = {
            "deploy": [
                {"name": "upload_jar", "title": "上传 Jar 包", "description": "将本地 Jar 包上传到远程服务器", "icon": "↑"},
                {"name": "restart_service", "title": "重启服务", "description": "重启 Docker Compose 服务容器", "icon": "⟳"},
                {"name": "download_log", "title": "下载日志", "description": "从服务器下载容器运行日志", "icon": "↓"},
                {"name": "oneclick_deploy", "title": "一键部署", "description": "自动完成上传、重启、下载全流程", "icon": "⚡"},
                {"name": "service_monitor", "title": "服务监控", "description": "监控 Docker 容器状态与性能", "icon": "♡"},
                {"name": "container_manager", "title": "容器管理", "description": "管理容器启动、停止、删除", "icon": "◫"},
            ],
            "database": [
                {"name": "sql_generator", "title": "SQL 生成器", "description": "连接数据库，智能生成复杂 SQL 查询", "icon": "⌘"},
                {"name": "db_compare", "title": "数据库对比", "description": "对比两个数据库的结构差异", "icon": "⇔"},
                {"name": "db_backup", "title": "数据备份", "description": "数据库备份与恢复工具", "icon": "◎"},
            ],
            "network": [
                {"name": "port_manager", "title": "端口管理", "description": "检测端口占用，释放指定端口", "icon": "⊕"},
                {"name": "ping_test", "title": "网络连通测试", "description": "测试服务器网络连通性和延迟", "icon": "◉"},
                {"name": "dns_lookup", "title": "DNS 查询", "description": "域名解析查询工具", "icon": "◎"},
            ],
            "format": [
                {"name": "file_converter", "title": "文件格式转换", "description": "PDF、Excel、Word、Markdown 互转", "icon": "↻"},
                {"name": "json_formatter", "title": "JSON 格式化", "description": "JSON 数据格式化、压缩、验证", "icon": "{ }"},
                {"name": "xml_formatter", "title": "XML 格式化", "description": "XML 数据格式化和验证", "icon": "< >"},
                {"name": "base64_tool", "title": "Base64 编解码", "description": "文本和文件的 Base64 编码解码", "icon": "#"},
                {"name": "timestamp_tool", "title": "时间戳转换", "description": "时间戳与日期时间互转", "icon": "◷"},
            ],
            "system": [
                {"name": "env_checker", "title": "环境检查", "description": "检查 Java、Docker、Node.js 等环境", "icon": "✓"},
                {"name": "process_manager", "title": "进程管理", "description": "查看和管理系统进程", "icon": "☰"},
                {"name": "disk_usage", "title": "磁盘分析", "description": "分析磁盘空间使用情况", "icon": "◌"},
            ],
        }

        self.category_meta = {
            "deploy": ("部署工具", "服务器部署与管理相关工具"),
            "database": ("数据库", "数据库连接、查询与管理"),
            "network": ("网络工具", "网络检测与端口管理"),
            "format": ("格式转换", "文件格式转换与数据格式化"),
            "system": ("系统工具", "环境检查与进程管理"),
        }

    def _on_nav_clicked(self, category):
        """导航点击"""
        # 更新导航状态
        for name, btn_data in self.nav_buttons.items():
            is_selected = name == category
            container = btn_data["container"]
            text_label = btn_data["text"]

            container.setStyleSheet(f"""
                QWidget#nav_{name} {{
                    background-color: {'#F5F3F0' if is_selected else 'transparent'};
                    border-radius: 10px;
                }}
                QWidget#nav_{name}:hover {{
                    background-color: {COLORS["nav_hover"]};
                }}
            """)

            text_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 14px;
                    font-weight: {'600' if is_selected else '500'};
                    color: {COLORS["nav_active"] if is_selected else COLORS["nav_inactive"]};
                    border: none;
                    background: transparent;
                }}
            """)

        # 更新标题
        title, desc = self.category_meta.get(category, ("工具", ""))
        self.section_title.setText(title)
        self.section_desc.setText(desc)

        # 显示卡片
        self._show_tools(category)

    def _show_tools(self, category):
        """显示工具卡片"""
        # 清空
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # 添加卡片
        tools = self.tools.get(category, [])
        for i, tool in enumerate(tools):
            card = ToolCard(
                name=tool["name"],
                title=tool["title"],
                description=tool["description"],
                icon_text=tool["icon"]
            )
            card.clicked.connect(self._on_tool_clicked)

            row = i // 3
            col = i % 3
            self.cards_layout.addWidget(card, row, col)

    def _on_tool_clicked(self, tool_name):
        """工具点击"""
        from ui.json_formatter_dialog import JsonFormatterDialog
        from ui.port_manager_dialog import PortManagerDialog
        from ui.sql_generator_dialog import SqlGeneratorDialog
        from ui.file_converter_dialog import FileConverterDialog

        if tool_name == "json_formatter":
            dlg = JsonFormatterDialog(self)
            dlg.exec()
        elif tool_name == "port_manager":
            dlg = PortManagerDialog(self)
            dlg.exec()
        elif tool_name == "sql_generator":
            dlg = SqlGeneratorDialog(self)
            dlg.exec()
        elif tool_name == "file_converter":
            dlg = FileConverterDialog(self)
            dlg.exec()
        elif tool_name in ["upload_jar", "restart_service", "download_log", "oneclick_deploy"]:
            from ui.main_window import MainWindow
            self.main_window = MainWindow()
            self.main_window.show()
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "提示", f"工具 {tool_name} 开发中...")
