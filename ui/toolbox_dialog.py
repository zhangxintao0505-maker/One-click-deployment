"""工具箱对话框 - 精致卡片式布局"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QWidget, QFrame,
    QGridLayout, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPainter, QPainterPath, QLinearGradient, QPalette


class ToolCard(QFrame):
    """工具卡片组件 - 精致版"""
    clicked = Signal(str)

    def __init__(self, name, title, description, icon_text="", color="#6366f1", parent=None):
        super().__init__(parent)
        self.tool_name = name
        self.icon_text = icon_text
        self.color = color
        self._title = title
        self._description = description
        self._is_hovered = False
        self._init_ui()

    def _init_ui(self):
        self.setFixedSize(280, 170)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # 基础样式
        self._update_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # 图标容器
        icon_container = QWidget()
        icon_container.setFixedSize(56, 56)
        icon_container.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.color}18, stop:1 {self.color}08);
                border-radius: 16px;
            }}
        """)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        icon_label = QLabel(self.icon_text)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 26px;
                border: none;
                background: transparent;
            }}
        """)
        icon_layout.addWidget(icon_label)
        layout.addWidget(icon_container)

        # 标题
        title = QLabel(self._title)
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 15px;
                font-weight: 600;
                color: #1e293b;
                border: none;
                background: transparent;
                letter-spacing: 0.3px;
            }}
        """)
        layout.addWidget(title)

        # 描述
        desc = QLabel(self._description)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: #64748b;
                border: none;
                background: transparent;
                line-height: 1.4;
            }}
        """)
        layout.addWidget(desc)

        layout.addStretch()

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 15))
        self.setGraphicsEffect(shadow)

    def _update_style(self):
        self.setStyleSheet(f"""
            ToolCard {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #fafbff);
                border: 1px solid #e2e8f0;
                border-radius: 20px;
                padding: 24px;
            }}
            ToolCard:hover {{
                border-color: {self.color}40;
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 {self.color}08);
            }}
        """)

    def enterEvent(self, event):
        self._is_hovered = True
        self._update_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self._update_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.tool_name)
        super().mousePressEvent(event)


class ToolboxDialog(QDialog):
    """工具箱对话框 - 精致版"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("工具箱")
        self.setMinimumSize(1050, 680)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 主容器
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8fafc, stop:0.5 #f1f5f9, stop:1 #e2e8f0);
            }
        """)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧导航栏
        nav_widget = QWidget()
        nav_widget.setFixedWidth(220)
        nav_widget.setStyleSheet("""
            QWidget {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8fafc);
                border-right: 1px solid #e2e8f0;
            }
        """)
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(20, 32, 20, 24)
        nav_layout.setSpacing(6)

        # Logo/标题
        logo_container = QWidget()
        logo_container.setStyleSheet("background: transparent;")
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(12, 0, 12, 24)

        logo_icon = QLabel("🧰")
        logo_icon.setStyleSheet("font-size: 28px; border: none; background: transparent;")
        logo_layout.addWidget(logo_icon)

        logo_text = QLabel("工具箱")
        logo_text.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: 700;
                color: #0f172a;
                border: none;
                background: transparent;
            }
        """)
        logo_layout.addWidget(logo_text)
        logo_layout.addStretch()

        nav_layout.addWidget(logo_container)

        # 分隔线
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #e2e8f0; border: none;")
        nav_layout.addWidget(sep)
        nav_layout.addSpacing(8)

        # 导航项
        nav_items = [
            ("deploy", "🚀", "部署工具"),
            ("database", "🗄️", "数据库"),
            ("network", "🌐", "网络工具"),
            ("format", "🎨", "格式化"),
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
                    border-radius: 12px;
                    padding: 12px 16px;
                }}
                QWidget#nav_{name}:hover {{
                    background-color: #f1f5f9;
                }}
            """)

            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(16, 12, 16, 12)
            btn_layout.setSpacing(12)

            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 20px; border: none; background: transparent;")
            btn_layout.addWidget(icon_label)

            text_label = QLabel(text)
            text_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: 500;
                    color: #475569;
                    border: none;
                    background: transparent;
                }
            """)
            btn_layout.addWidget(text_label)
            btn_layout.addStretch()

            btn_container.mousePressEvent = lambda event, n=name: self._on_nav_clicked(n)
            self.nav_buttons[name] = btn_container
            nav_layout.addWidget(btn_container)

        nav_layout.addStretch()

        # 版本信息
        version_label = QLabel("v1.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #94a3b8;
                border: none;
                background: transparent;
                padding: 8px;
            }
        """)
        nav_layout.addWidget(version_label)

        main_layout.addWidget(nav_widget)

        # 右侧内容区
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 36, 40, 32)
        content_layout.setSpacing(28)

        # 标题区域
        header_widget = QWidget()
        header_widget.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        self.section_title = QLabel("部署工具")
        self.section_title.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: 700;
                color: #0f172a;
                border: none;
                background: transparent;
                letter-spacing: -0.5px;
            }
        """)
        header_layout.addWidget(self.section_title)

        self.section_desc = QLabel("服务器部署与管理相关工具")
        self.section_desc.setStyleSheet("""
            QLabel {
                font-size: 15px;
                color: #64748b;
                border: none;
                background: transparent;
            }
        """)
        header_layout.addWidget(self.section_desc)

        content_layout.addWidget(header_widget)

        # 进度指示器（可选）
        progress_widget = QWidget()
        progress_widget.setFixedHeight(4)
        progress_widget.setStyleSheet("""
            QWidget {
                background-color: #e2e8f0;
                border-radius: 2px;
                border: none;
            }
        """)
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_bar = QWidget()
        self.progress_bar.setStyleSheet("""
            QWidget {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                border-radius: 2px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        content_layout.addWidget(progress_widget)

        # 工具卡片区域（滚动）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                width: 6px;
                background: transparent;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                border-radius: 3px;
                min-height: 50px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(24)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll_area.setWidget(self.cards_container)
        content_layout.addWidget(scroll_area)

        # 底部导航
        bottom_widget = QWidget()
        bottom_widget.setStyleSheet("background: transparent;")
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # 分页指示器
        self.page_dots = QHBoxLayout()
        self.page_dots.setSpacing(8)
        self.page_dots.addStretch()

        for i in range(2):
            dot = QWidget()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"""
                QWidget {{
                    background-color: {'#6366f1' if i == 0 else '#cbd5e1'};
                    border-radius: 4px;
                }}
            """)
            self.page_dots.addWidget(dot)

        self.page_dots.addStretch()
        bottom_layout.addLayout(self.page_dots)

        # 翻页按钮
        nav_btn_style = """
            QPushButton {
                background-color: #f1f5f9;
                border: 1px solid #e2e8f0;
                border-radius: 20px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """

        self.prev_btn = QPushButton("‹")
        self.prev_btn.setFixedSize(40, 40)
        self.prev_btn.setStyleSheet(nav_btn_style)
        bottom_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("›")
        self.next_btn.setFixedSize(40, 40)
        self.next_btn.setStyleSheet(nav_btn_style)
        bottom_layout.addWidget(self.next_btn)

        content_layout.addWidget(bottom_widget)

        main_layout.addWidget(content_widget)

        layout.addWidget(main_widget)

        # 初始化工具卡片
        self._init_tools()
        self._on_nav_clicked("deploy")

    def _init_tools(self):
        """初始化所有工具卡片"""
        self.tools = {
            "deploy": [
                {
                    "name": "upload_jar",
                    "title": "上传 Jar 包",
                    "description": "将本地 Jar 包上传到远程服务器",
                    "icon": "📦",
                    "color": "#6366f1"
                },
                {
                    "name": "restart_service",
                    "title": "重启服务",
                    "description": "重启 Docker Compose 服务容器",
                    "icon": "🔄",
                    "color": "#8b5cf6"
                },
                {
                    "name": "download_log",
                    "title": "下载日志",
                    "description": "从服务器下载容器运行日志",
                    "icon": "📥",
                    "color": "#0ea5e9"
                },
                {
                    "name": "oneclick_deploy",
                    "title": "一键部署",
                    "description": "自动完成Jar包上传、解压、重启容器等。",
                    "icon": "⚡",
                    "color": "#f59e0b"
                },
                {
                    "name": "service_monitor",
                    "title": "服务监控",
                    "description": "监控 Docker 容器状态与性能",
                    "icon": "📊",
                    "color": "#10b981"
                },
                {
                    "name": "container_manager",
                    "title": "容器管理",
                    "description": "管理容器启动、停止、删除",
                    "icon": "🐳",
                    "color": "#0ea5e9"
                },
            ],
            "database": [
                {
                    "name": "sql_generator",
                    "title": "SQL 生成器",
                    "description": "连接数据库，智能生成复杂 SQL 查询",
                    "icon": "🗄️",
                    "color": "#8b5cf6"
                },
                {
                    "name": "db_compare",
                    "title": "数据库对比",
                    "description": "对比两个数据库的结构差异",
                    "icon": "🔄",
                    "color": "#ec4899"
                },
                {
                    "name": "db_backup",
                    "title": "数据备份",
                    "description": "数据库备份与恢复工具",
                    "icon": "💾",
                    "color": "#06b6d4"
                },
            ],
            "network": [
                {
                    "name": "port_manager",
                    "title": "端口管理",
                    "description": "检测端口占用，释放指定端口",
                    "icon": "🔌",
                    "color": "#ef4444"
                },
                {
                    "name": "ping_test",
                    "title": "网络连通测试",
                    "description": "测试服务器网络连通性和延迟",
                    "icon": "📡",
                    "color": "#10b981"
                },
                {
                    "name": "dns_lookup",
                    "title": "DNS 查询",
                    "description": "域名解析查询工具",
                    "icon": "🌐",
                    "color": "#6366f1"
                },
            ],
            "format": [
                {
                    "name": "file_converter",
                    "title": "文件格式转换",
                    "description": "PDF、Excel、Word、Markdown 互转",
                    "icon": "🔄",
                    "color": "#6366f1"
                },
                {
                    "name": "json_formatter",
                    "title": "JSON 格式化",
                    "description": "JSON 数据格式化、压缩、验证",
                    "icon": "📝",
                    "color": "#06b6d4"
                },
                {
                    "name": "xml_formatter",
                    "title": "XML 格式化",
                    "description": "XML 数据格式化和验证",
                    "icon": "📋",
                    "color": "#f59e0b"
                },
                {
                    "name": "base64_tool",
                    "title": "Base64 编解码",
                    "description": "文本和文件的 Base64 编码解码",
                    "icon": "🔐",
                    "color": "#8b5cf6"
                },
                {
                    "name": "timestamp_tool",
                    "title": "时间戳转换",
                    "description": "时间戳与日期时间互转",
                    "icon": "⏰",
                    "color": "#ef4444"
                },
            ],
            "system": [
                {
                    "name": "env_checker",
                    "title": "环境检查",
                    "description": "检查 Java、Docker、Node.js 等环境",
                    "icon": "🔍",
                    "color": "#3b82f6"
                },
                {
                    "name": "process_manager",
                    "title": "进程管理",
                    "description": "查看和管理系统进程",
                    "icon": "📊",
                    "color": "#10b981"
                },
                {
                    "name": "disk_usage",
                    "title": "磁盘分析",
                    "description": "分析磁盘空间使用情况",
                    "icon": "💿",
                    "color": "#6366f1"
                },
            ],
        }

        # 分类元数据
        self.category_meta = {
            "deploy": ("部署工具", "服务器部署与管理相关工具"),
            "database": ("数据库", "数据库连接、查询与管理"),
            "network": ("网络工具", "网络检测与端口管理"),
            "format": ("格式化", "文件格式转换与数据格式化工具"),
            "system": ("系统工具", "环境检查与进程管理"),
        }

    def _on_nav_clicked(self, category):
        """导航栏点击事件"""
        # 更新导航按钮状态
        for name, container in self.nav_buttons.items():
            is_selected = name == category
            container.setStyleSheet(f"""
                QWidget#nav_{name} {{
                    background-color: {'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ede9fe, stop:1 #e0e7ff)' if is_selected else 'transparent'};
                    border-radius: 12px;
                    padding: 12px 16px;
                }}
                QWidget#nav_{name}:hover {{
                    background-color: {'#ede9fe' if is_selected else '#f1f5f9'};
                }}
            """)
            # 更新文字颜色
            for child in container.findChildren(QLabel):
                if child.text() in ["🚀", "🗄️", "🌐", "🎨", "⚙️"]:
                    continue
                child.setStyleSheet(f"""
                    QLabel {{
                        font-size: 14px;
                        font-weight: {'700' if is_selected else '500'};
                        color: {'#6366f1' if is_selected else '#475569'};
                        border: none;
                        background: transparent;
                    }}
                """)

        # 更新标题
        title, desc = self.category_meta.get(category, ("工具", ""))
        self.section_title.setText(title)
        self.section_desc.setText(desc)

        # 更新卡片
        self._show_tools(category)

    def _show_tools(self, category):
        """显示指定分类的工具卡片"""
        # 清空现有卡片
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # 获取工具列表
        tools = self.tools.get(category, [])

        # 添加卡片
        for i, tool in enumerate(tools):
            card = ToolCard(
                name=tool["name"],
                title=tool["title"],
                description=tool["description"],
                icon_text=tool["icon"],
                color=tool["color"]
            )
            card.clicked.connect(self._on_tool_clicked)

            row = i // 3
            col = i % 3
            self.cards_layout.addWidget(card, row, col)

    def _on_tool_clicked(self, tool_name):
        """工具卡片点击事件"""
        # 根据工具名称打开对应的对话框
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
