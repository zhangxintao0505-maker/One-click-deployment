"""主窗口 - iOS 极简风 + Claude 暖色调"""
import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QTextEdit, QPushButton, QCheckBox, QLabel, QGroupBox, QSplitter,
    QStatusBar, QMessageBox, QListWidgetItem, QLineEdit, QFormLayout,
    QFileDialog, QScrollArea, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QAction

from config_manager import load_config, save_config, load_services, save_services
from ssh_worker import UploadWorker, RestartWorker, DownloadWorker
from ui.settings_dialog import SettingsDialog
from ui.services_dialog import ServicesDialog


# ═══════════════════════════════════════════════════════════════
# iOS 风格配色
# ═══════════════════════════════════════════════════════════════
COLORS = {
    "bg": "#FBF9F6",
    "card": "#FFFFFF",
    "card_border": "#EBE7E0",
    "title": "#222220",
    "desc": "#8C867E",
    "accent": "#0099ff",
    "divider": "#EBE7E0",
}

# 通用样式
INPUT_STYLE = f"""
    QLineEdit, QTextEdit {{
        border: 1px solid {COLORS["card_border"]};
        border-radius: 10px;
        padding: 10px 14px;
        font-size: 14px;
        background-color: {COLORS["card"]};
        color: {COLORS["title"]};
        selection-background-color: {COLORS["accent"]}40;
    }}
    QLineEdit:focus, QTextEdit:focus {{
        border-color: {COLORS["accent"]};
    }}
"""

LABEL_STYLE = f"""
    color: {COLORS["desc"]};
    font-size: 13px;
    border: none;
    background: transparent;
"""

TITLE_STYLE = f"""
    font-size: 15px;
    font-weight: 600;
    color: {COLORS["title"]};
    border: none;
    background: transparent;
"""

CARD_STYLE = f"""
    QWidget {{
        background-color: {COLORS["card"]};
        border: 1px solid {COLORS["card_border"]};
        border-radius: 16px;
    }}
"""

BTN_PRIMARY = f"""
    QPushButton {{
        background-color: {COLORS["accent"]};
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 600;
        font-size: 14px;
    }}
    QPushButton:hover {{
        background-color: #0080e6;
    }}
    QPushButton:disabled {{
        background-color: #ccc;
    }}
"""

BTN_SECONDARY = f"""
    QPushButton {{
        background-color: {COLORS["card"]};
        color: {COLORS["title"]};
        border: 1px solid {COLORS["card_border"]};
        border-radius: 10px;
        padding: 10px 16px;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: #F5F3F0;
    }}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("一键部署工具")
        self.setMinimumSize(1050, 680)

        self.config = load_config()
        self.services = load_services()
        self.current_service = None
        self.history = []
        self.workers = []

        self._init_ui()
        self._init_menu()
        self._refresh_service_list()

    def _init_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # ═══════════════════════════════════════════════════════════
        # 左侧服务列表
        # ═══════════════════════════════════════════════════════════
        left = QWidget()
        left.setObjectName("left_panel")
        left.setStyleSheet(f"""
            QWidget#left_panel {{
                background-color: {COLORS["card"]};
                border: 1px solid {COLORS["card_border"]};
                border-radius: 16px;
            }}
        """)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 20, 16, 16)
        left_layout.setSpacing(12)

        # 标题
        left_header = QHBoxLayout()
        left_label = QLabel("服务环境列表")
        left_label.setStyleSheet(TITLE_STYLE)
        left_header.addWidget(left_label)

        self.add_service_btn = QPushButton("+")
        self.add_service_btn.setFixedSize(28, 28)
        self.add_service_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["accent"]};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: #0080e6;
            }}
        """)
        self.add_service_btn.clicked.connect(self._add_service)
        left_header.addWidget(self.add_service_btn)
        left_header.addStretch()
        left_layout.addLayout(left_header)

        # 服务列表
        self.service_list = QListWidget()
        self.service_list.setStyleSheet(f"""
            QListWidget {{
                border: none;
                background-color: transparent;
                padding: 0;
            }}
            QListWidget::item {{
                padding: 12px;
                margin: 4px 0;
                border-radius: 10px;
                border: none;
                background-color: transparent;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS["accent"]}15;
                color: {COLORS["accent"]};
            }}
            QListWidget::item:hover {{
                background-color: #F5F3F0;
            }}
        """)
        self.service_list.currentRowChanged.connect(self._on_service_selected)
        left_layout.addWidget(self.service_list)

        # 全局设置按钮
        self.global_settings_btn = QPushButton("⚙  全局设置")
        self.global_settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS["desc"]};
                border: 1px solid {COLORS["card_border"]};
                border-radius: 10px;
                padding: 12px;
                text-align: left;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #F5F3F0;
                color: {COLORS["title"]};
            }}
        """)
        self.global_settings_btn.clicked.connect(self._open_settings)
        left_layout.addWidget(self.global_settings_btn)

        main_layout.addWidget(left, 1)

        # ═══════════════════════════════════════════════════════════
        # 右侧面板
        # ═══════════════════════════════════════════════════════════
        right = QWidget()
        right.setStyleSheet(f"background: transparent;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)

        # 服务详情卡片
        detail_card = QWidget()
        detail_card.setObjectName("detail_card")
        detail_card.setStyleSheet(f"""
            QWidget#detail_card {{
                background-color: {COLORS["card"]};
                border: 1px solid {COLORS["card_border"]};
                border-radius: 16px;
            }}
        """)
        detail_layout = QVBoxLayout(detail_card)
        detail_layout.setContentsMargins(24, 24, 24, 24)
        detail_layout.setSpacing(20)

        # 服务器与网络属性
        section1_title = QLabel("服务器与网络属性")
        section1_title.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 600;
            color: {COLORS["title"]};
            padding-left: 12px;
            border-left: 3px solid {COLORS["accent"]};
        """)
        detail_layout.addWidget(section1_title)

        # 服务名称、SSH主机、用户名
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        self.detail_fields = {}

        for label_text, field_key, placeholder in [
            ("服务名称", "service_name", "请输入服务名称"),
            ("SSH 主机 IP", "ssh_host", "默认全局IP"),
            ("SSH 登录用户名", "ssh_user", "默认全局用户"),
        ]:
            field_widget = QWidget()
            field_layout = QVBoxLayout(field_widget)
            field_layout.setContentsMargins(0, 0, 0, 0)
            field_layout.setSpacing(6)

            label = QLabel(label_text)
            label.setStyleSheet(LABEL_STYLE)
            field_layout.addWidget(label)

            edit = QLineEdit()
            edit.setPlaceholderText(placeholder)
            edit.setStyleSheet(INPUT_STYLE)
            field_layout.addWidget(edit)
            self.detail_fields[field_key] = edit

            row1.addWidget(field_widget)

        detail_layout.addLayout(row1)

        # 部署制品与容器设定
        section2_title = QLabel("部署制品与容器设定")
        section2_title.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 600;
            color: {COLORS["title"]};
            padding-left: 12px;
            border-left: 3px solid {COLORS["accent"]};
            margin-top: 8px;
        """)
        detail_layout.addWidget(section2_title)

        # 本地Jar路径 + 服务器路径
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        # 本地Jar路径
        jar_widget = QWidget()
        jar_layout = QVBoxLayout(jar_widget)
        jar_layout.setContentsMargins(0, 0, 0, 0)
        jar_layout.setSpacing(6)

        jar_label = QLabel("本地制品包 (Jar) 路径")
        jar_label.setStyleSheet(LABEL_STYLE)
        jar_layout.addWidget(jar_label)

        jar_row = QHBoxLayout()
        jar_row.setSpacing(8)
        local_jar_edit = QLineEdit()
        local_jar_edit.setPlaceholderText("浏览或输入路径")
        local_jar_edit.setStyleSheet(INPUT_STYLE)
        jar_row.addWidget(local_jar_edit)
        self.detail_fields["local_jar_path"] = local_jar_edit

        jar_browse = QPushButton("浏览...")
        jar_browse.setFixedWidth(70)
        jar_browse.setStyleSheet(BTN_SECONDARY)
        jar_browse.clicked.connect(lambda: self._browse_field("local_jar_path", local_jar_edit))
        jar_row.addWidget(jar_browse)
        jar_layout.addLayout(jar_row)

        row2.addWidget(jar_widget, 2)

        # 服务器路径
        remote_widget = QWidget()
        remote_layout = QVBoxLayout(remote_widget)
        remote_layout.setContentsMargins(0, 0, 0, 0)
        remote_layout.setSpacing(6)

        remote_label = QLabel("服务器存储 Jar 绝对路径")
        remote_label.setStyleSheet(LABEL_STYLE)
        remote_layout.addWidget(remote_label)

        remote_edit = QLineEdit()
        remote_edit.setPlaceholderText("/data/jar")
        remote_edit.setStyleSheet(INPUT_STYLE)
        remote_layout.addWidget(remote_edit)
        self.detail_fields["remote_jar_dir"] = remote_edit

        row2.addWidget(remote_widget, 1)
        detail_layout.addLayout(row2)

        # Docker Compose 配置
        row3 = QHBoxLayout()
        row3.setSpacing(16)

        for label_text, field_key, placeholder in [
            ("Docker Compose 运行目录", "compose_dir", "/data/app"),
            ("Docker Compose 服务标识", "compose_service_name", "例如: contract"),
        ]:
            field_widget = QWidget()
            field_layout = QVBoxLayout(field_widget)
            field_layout.setContentsMargins(0, 0, 0, 0)
            field_layout.setSpacing(6)

            label = QLabel(label_text)
            label.setStyleSheet(LABEL_STYLE)
            field_layout.addWidget(label)

            edit = QLineEdit()
            edit.setPlaceholderText(placeholder)
            edit.setStyleSheet(INPUT_STYLE)
            field_layout.addWidget(edit)
            self.detail_fields[field_key] = edit

            row3.addWidget(field_widget)

        detail_layout.addLayout(row3)

        # 保存按钮
        save_row = QHBoxLayout()
        save_row.addStretch()
        save_detail_btn = QPushButton("保存配置修改")
        save_detail_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["card"]};
                color: {COLORS["title"]};
                border: 1px solid {COLORS["card_border"]};
                border-radius: 10px;
                padding: 10px 24px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #F5F3F0;
            }}
        """)
        save_detail_btn.clicked.connect(self._save_detail)
        save_row.addWidget(save_detail_btn)
        detail_layout.addLayout(save_row)

        right_layout.addWidget(detail_card)

        # ═══════════════════════════════════════════════════════════
        # 操作按钮区
        # ═══════════════════════════════════════════════════════════
        ops_card = QWidget()
        ops_card.setObjectName("ops_card")
        ops_card.setStyleSheet(f"""
            QWidget#ops_card {{
                background-color: {COLORS["card"]};
                border: 1px solid {COLORS["card_border"]};
                border-radius: 16px;
            }}
        """)
        ops_layout = QHBoxLayout(ops_card)
        ops_layout.setContentsMargins(20, 16, 20, 16)
        ops_layout.setSpacing(12)

        self.upload_btn = QPushButton("↑ 上传 Jar 包")
        self.upload_btn.setStyleSheet(BTN_SECONDARY)
        self.upload_btn.clicked.connect(self._do_upload)
        ops_layout.addWidget(self.upload_btn)

        self.restart_btn = QPushButton("⟳ 重启容器")
        self.restart_btn.setStyleSheet(BTN_SECONDARY)
        self.restart_btn.clicked.connect(self._do_restart)
        ops_layout.addWidget(self.restart_btn)

        self.download_btn = QPushButton("↓ 下载日志")
        self.download_btn.setStyleSheet(BTN_SECONDARY)
        self.download_btn.clicked.connect(self._do_download)
        ops_layout.addWidget(self.download_btn)

        self.archive_cb = QCheckBox("时间戳备份归档")
        self.archive_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS["desc"]};
                font-size: 13px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid {COLORS["card_border"]};
                background-color: {COLORS["card"]};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS["accent"]};
                border-color: {COLORS["accent"]};
            }}
        """)
        ops_layout.addWidget(self.archive_cb)

        ops_layout.addStretch()

        self.oneclick_btn = QPushButton("⚡ 一键全部部署")
        self.oneclick_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS["accent"]}, stop:1 #7C4DFF);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 28px;
                font-weight: bold;
                font-size: 15px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0080e6, stop:1 #6a3de8);
            }}
        """)
        self.oneclick_btn.clicked.connect(self._do_oneclick)
        ops_layout.addWidget(self.oneclick_btn)

        right_layout.addWidget(ops_card)

        # ═══════════════════════════════════════════════════════════
        # 日志区
        # ═══════════════════════════════════════════════════════════
        log_card = QWidget()
        log_card.setObjectName("log_card")
        log_card.setStyleSheet(f"""
            QWidget#log_card {{
                background-color: #1e1e2e;
                border-radius: 16px;
            }}
        """)
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(0)

        log_header = QWidget()
        log_header.setStyleSheet("""
            background-color: #2d2d3f;
            border-top-left-radius: 16px;
            border-top-right-radius: 16px;
        """)
        log_header_layout = QHBoxLayout(log_header)
        log_header_layout.setContentsMargins(20, 12, 20, 12)

        log_title = QLabel("▶_ Deployment Log")
        log_title.setStyleSheet("""
            color: #00ff88;
            font-family: Consolas, monospace;
            font-size: 13px;
            font-weight: bold;
            border: none;
            background: transparent;
        """)
        log_header_layout.addWidget(log_title)
        log_header_layout.addStretch()

        clear_btn = QPushButton("清空屏幕")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                color: white;
            }
        """)
        clear_btn.clicked.connect(lambda: self.log_text.clear())
        log_header_layout.addWidget(clear_btn)
        log_layout.addWidget(log_header)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #d4d4d4;
                border: none;
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
                padding: 16px;
            }
        """)
        log_layout.addWidget(self.log_text)

        right_layout.addWidget(log_card, 1)

        main_layout.addWidget(right, 3)

        # 状态栏
        self.statusBar().setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS["bg"]};
                border: none;
                padding: 4px 12px;
                color: {COLORS["desc"]};
            }}
        """)
        self.statusBar().showMessage("就绪")

    def _init_menu(self):
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {COLORS["bg"]};
                border: none;
                padding: 4px 0;
                color: {COLORS["title"]};
            }}
            QMenuBar::item {{
                padding: 8px 16px;
                border-radius: 8px;
            }}
            QMenuBar::item:selected {{
                background-color: #F5F3F0;
            }}
            QMenu {{
                background-color: {COLORS["card"]};
                border: 1px solid {COLORS["card_border"]};
                border-radius: 10px;
                padding: 8px;
            }}
            QMenu::item {{
                padding: 8px 24px;
                border-radius: 6px;
            }}
            QMenu::item:selected {{
                background-color: #F5F3F0;
            }}
        """)

        file_menu = menu_bar.addMenu("文件")
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        services_action = QAction("服务管理", self)
        services_action.triggered.connect(self._open_services)
        file_menu.addAction(services_action)

        file_menu.addSeparator()
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menu_bar.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        history_menu = menu_bar.addMenu("历史")
        show_history_action = QAction("查看操作历史", self)
        show_history_action.triggered.connect(self._show_history)
        history_menu.addAction(show_history_action)

        # 工具菜单
        tools_menu = menu_bar.addMenu("工具")

        from ui.json_formatter_dialog import JsonFormatterDialog
        from ui.port_manager_dialog import PortManagerDialog
        from ui.sql_generator_dialog import SqlGeneratorDialog

        json_formatter_action = QAction("JSON 格式化", self)
        json_formatter_action.triggered.connect(lambda: JsonFormatterDialog(self).exec())
        tools_menu.addAction(json_formatter_action)

        port_manager_action = QAction("端口管理", self)
        port_manager_action.triggered.connect(lambda: PortManagerDialog(self).exec())
        tools_menu.addAction(port_manager_action)

        sql_generator_action = QAction("SQL 生成器", self)
        sql_generator_action.triggered.connect(lambda: SqlGeneratorDialog(self).exec())
        tools_menu.addAction(sql_generator_action)

    def _add_service(self):
        """添加新服务"""
        new_service = {
            "service_name": f"新服务 {len(self.services) + 1}",
            "ssh_host": "",
            "ssh_user": "",
            "local_jar_path": "",
            "remote_jar_dir": "",
            "compose_dir": "",
            "compose_service_name": "",
            "remote_log_path": "",
            "local_log_dir": "",
        }
        self.services.append(new_service)
        save_services(self.services)
        self._refresh_service_list()
        self.service_list.setCurrentRow(len(self.services) - 1)
        self._append_log(f"[服务] 已添加新服务: {new_service['service_name']}")
        self.statusBar().showMessage("新服务已添加")

    def _refresh_service_list(self):
        self.service_list.clear()
        for svc in self.services:
            item = QListWidgetItem(svc.get("service_name", "未命名"))
            self.service_list.addItem(item)
        if self.services:
            self.service_list.setCurrentRow(0)
        else:
            self.current_service = None
            for edit in self.detail_fields.values():
                edit.clear()
                edit.setEnabled(False)

    def _on_service_selected(self, row):
        if row < 0 or row >= len(self.services):
            self.current_service = None
            for edit in self.detail_fields.values():
                edit.clear()
                edit.setEnabled(False)
            return
        self.current_service = self.services[row]
        svc = self.current_service
        for key, edit in self.detail_fields.items():
            edit.setEnabled(True)
            edit.setText(svc.get(key, ""))

    def _browse_field(self, key, edit):
        if key == "local_jar_path":
            path, _ = QFileDialog.getOpenFileName(self, "选择Jar文件", "", "Jar文件 (*.jar);;所有文件 (*)")
        else:
            path = QFileDialog.getExistingDirectory(self, "选择目录")
        if path:
            edit.setText(path)

    def _save_detail(self):
        if not self.current_service:
            return
        row = self.service_list.currentRow()
        if row < 0:
            return
        for key, edit in self.detail_fields.items():
            self.current_service[key] = edit.text().strip()
        self.services[row] = self.current_service
        save_services(self.services)
        self.service_list.blockSignals(True)
        self.service_list.currentItem().setText(self.current_service.get("service_name", "未命名"))
        self.service_list.blockSignals(False)
        self.statusBar().showMessage("服务配置已保存")

    def _set_buttons_enabled(self, enabled):
        self.upload_btn.setEnabled(enabled)
        self.restart_btn.setEnabled(enabled)
        self.download_btn.setEnabled(enabled)
        self.oneclick_btn.setEnabled(enabled)
        self.add_service_btn.setEnabled(enabled)

    def _append_log(self, text):
        self.log_text.append(text)
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _add_history(self, service_name, action, result):
        entry = {
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "service": service_name,
            "action": action,
            "result": result,
        }
        self.history.insert(0, entry)
        if len(self.history) > 20:
            self.history = self.history[:20]

    def _do_upload(self):
        if not self.current_service:
            QMessageBox.warning(self, "提示", "请先选择一个服务")
            return
        self._set_buttons_enabled(False)
        self.statusBar().showMessage("正在上传...")
        self._append_log(f"\n{'='*40}")
        self._append_log(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 开始上传 Jar 包")

        worker = UploadWorker(self.config, self.current_service)
        worker.log.connect(self._append_log)
        worker.progress.connect(self._on_upload_progress)
        worker.finished_ok.connect(lambda ok, msg: self._on_task_finished("上传Jar", ok, msg))
        self.workers.append(worker)
        worker.start()

    def _on_upload_progress(self, transferred, total):
        if total > 0:
            pct = int(transferred * 100 / total)
            self.statusBar().showMessage(f"上传进度: {pct}%")

    def _do_restart(self):
        if not self.current_service:
            QMessageBox.warning(self, "提示", "请先选择一个服务")
            return
        self._set_buttons_enabled(False)
        self.statusBar().showMessage("正在重启服务...")
        self._append_log(f"\n{'='*40}")
        self._append_log(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 开始重启服务")

        worker = RestartWorker(self.config, self.current_service)
        worker.log.connect(self._append_log)
        worker.finished_ok.connect(lambda ok, msg: self._on_task_finished("重启服务", ok, msg))
        self.workers.append(worker)
        worker.start()

    def _do_download(self):
        if not self.current_service:
            QMessageBox.warning(self, "提示", "请先选择一个服务")
            return
        self._set_buttons_enabled(False)
        self.statusBar().showMessage("正在下载日志...")
        self._append_log(f"\n{'='*40}")
        self._append_log(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 开始下载日志")

        archive = self.archive_cb.isChecked()
        worker = DownloadWorker(self.config, self.current_service, archive=archive)
        worker.log.connect(self._append_log)
        worker.progress.connect(self._on_download_progress)
        worker.finished_ok.connect(lambda ok, msg: self._on_task_finished("下载日志", ok, msg))
        self.workers.append(worker)
        worker.start()

    def _on_download_progress(self, current, total):
        if total > 0:
            self.statusBar().showMessage(f"下载进度: {current}/{total}")

    def _do_oneclick(self):
        if not self.current_service:
            QMessageBox.warning(self, "提示", "请先选择一个服务")
            return
        self._set_buttons_enabled(False)
        self._append_log(f"\n{'='*40}")
        self._append_log(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 开始一键部署")
        self._oneclick_step = 0
        self._run_oneclick_step()

    def _run_oneclick_step(self):
        svc = self.current_service
        if self._oneclick_step == 0:
            self.statusBar().showMessage("一键部署: 正在上传...")
            self._append_log("\n--- 步骤 1/3: 上传 Jar 包 ---")
            worker = UploadWorker(self.config, svc)
            worker.log.connect(self._append_log)
            worker.progress.connect(self._on_upload_progress)
            worker.finished_ok.connect(self._oneclick_step_done)
            self.workers.append(worker)
            worker.start()
        elif self._oneclick_step == 1:
            self.statusBar().showMessage("一键部署: 正在重启...")
            self._append_log("\n--- 步骤 2/3: 重启服务 ---")
            worker = RestartWorker(self.config, svc)
            worker.log.connect(self._append_log)
            worker.finished_ok.connect(self._oneclick_step_done)
            self.workers.append(worker)
            worker.start()
        elif self._oneclick_step == 2:
            self.statusBar().showMessage("一键部署: 正在下载日志...")
            self._append_log("\n--- 步骤 3/3: 下载日志 ---")
            archive = self.archive_cb.isChecked()
            worker = DownloadWorker(self.config, svc, archive=archive)
            worker.log.connect(self._append_log)
            worker.progress.connect(self._on_download_progress)
            worker.finished_ok.connect(self._oneclick_step_done)
            self.workers.append(worker)
            worker.start()
        else:
            self._append_log("\n✅ 一键部署全部完成!")
            self._add_history(svc.get("service_name", ""), "一键部署", "成功")
            self._set_buttons_enabled(True)
            self.statusBar().showMessage("一键部署完成")

    def _oneclick_step_done(self, ok, msg):
        step_names = ["上传Jar", "重启服务", "下载日志"]
        step_name = step_names[self._oneclick_step]
        if ok:
            self._append_log(f"✅ {step_name}: {msg}")
        else:
            self._append_log(f"❌ {step_name}: {msg}")
            self._add_history(self.current_service.get("service_name", ""), "一键部署", f"{step_name}失败: {msg}")
            self._set_buttons_enabled(True)
            self.statusBar().showMessage(f"一键部署失败: {step_name}")
            return
        self._oneclick_step += 1
        QTimer.singleShot(500, self._run_oneclick_step)

    def _on_task_finished(self, action, ok, msg):
        svc_name = self.current_service.get("service_name", "") if self.current_service else ""
        result = "成功" if ok else f"失败: {msg}"
        self._add_history(svc_name, action, result)
        self._set_buttons_enabled(True)
        if ok:
            self.statusBar().showMessage(f"{action} 完成")
        else:
            self.statusBar().showMessage(f"{action} 失败")

    def _open_settings(self):
        dlg = SettingsDialog(self.config, self)
        if dlg.exec() == SettingsDialog.Accepted:
            self.config = dlg.get_config()
            save_config(self.config)
            self._append_log("[设置] 配置已保存")

    def _open_services(self):
        dlg = ServicesDialog(self.services, self)
        if dlg.exec() == ServicesDialog.Accepted:
            self.services = dlg.get_services()
            save_services(self.services)
            self._refresh_service_list()
            self._append_log("[服务] 服务列表已更新")

    def _show_about(self):
        QMessageBox.about(
            self, "关于",
            "一键部署工具 v1.0\n\n"
            "Windows 桌面端部署管理工具\n"
            "支持上传Jar包、重启Docker服务、下载日志\n\n"
            "技术栈: Python 3 + PySide6 + Paramiko"
        )

    def _show_history(self):
        if not self.history:
            QMessageBox.information(self, "操作历史", "暂无操作记录")
            return
        lines = ["最近操作记录:\n"]
        for h in self.history:
            lines.append(f"[{h['time']}] {h['service']} - {h['action']} - {h['result']}")
        QMessageBox.information(self, "操作历史", "\n".join(lines))
