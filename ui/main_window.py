import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QTextEdit, QPushButton, QCheckBox, QLabel, QGroupBox, QSplitter,
    QStatusBar, QMessageBox, QListWidgetItem, QLineEdit, QFormLayout,
    QFileDialog, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QAction

from config_manager import load_config, save_config, load_services, save_services
from ssh_worker import UploadWorker, RestartWorker, DownloadWorker
from ui.settings_dialog import SettingsDialog
from ui.services_dialog import ServicesDialog
from ui.json_formatter_dialog import JsonFormatterDialog
from ui.port_manager_dialog import PortManagerDialog
from ui.sql_generator_dialog import SqlGeneratorDialog
from ui.toolbox_dialog import ToolboxDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("一键部署工具")
        self.setMinimumSize(1000, 650)

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
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧服务列表
        left = QWidget()
        left.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-right: 1px solid #e9ecef;
            }
        """)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 16, 12, 12)

        left_header = QHBoxLayout()
        left_label = QLabel("服务环境列表")
        left_label.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            color: #333;
            padding: 8px 0;
        """)
        left_header.addWidget(left_label)

        self.add_service_btn = QPushButton("+")
        self.add_service_btn.setFixedSize(28, 28)
        self.add_service_btn.setStyleSheet("""
            QPushButton {
                background-color: #0099ff;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #0080e6;
            }
        """)
        self.add_service_btn.clicked.connect(self._add_service)
        left_header.addWidget(self.add_service_btn)
        left_header.addStretch()
        left_layout.addLayout(left_header)

        self.service_list = QListWidget()
        self.service_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                padding: 4px;
            }
            QListWidget::item {
                padding: 10px 12px;
                margin: 4px 0;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                border-left: 3px solid #0099ff;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        self.service_list.currentRowChanged.connect(self._on_service_selected)
        left_layout.addWidget(self.service_list)

        # 全局设置按钮
        self.global_settings_btn = QPushButton("⚙ 全局设置")
        self.global_settings_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #666;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #0099ff;
            }
        """)
        self.global_settings_btn.clicked.connect(self._open_settings)
        left_layout.addWidget(self.global_settings_btn)

        splitter.addWidget(left)

        # 右侧面板
        right = QWidget()
        right.setStyleSheet("background-color: white;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(24, 20, 24, 20)
        right_layout.setSpacing(20)

        # 服务详情配置区
        detail_container = QWidget()
        detail_container.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)
        detail_outer_layout = QVBoxLayout(detail_container)
        detail_outer_layout.setContentsMargins(0, 0, 0, 0)

        # 服务器与网络属性标题
        detail_title = QLabel("服务器与网络属性")
        detail_title.setStyleSheet("""
            font-weight: bold;
            font-size: 13px;
            color: #333;
            padding-left: 12px;
            border-left: 3px solid #0099ff;
            margin-bottom: 12px;
        """)
        detail_outer_layout.addWidget(detail_title)

        # 服务器字段
        server_grid = QWidget()
        server_grid_layout = QHBoxLayout(server_grid)
        server_grid_layout.setContentsMargins(0, 0, 0, 0)
        server_grid_layout.setSpacing(20)

        # 服务名称
        svc_name_group = QWidget()
        svc_name_layout = QVBoxLayout(svc_name_group)
        svc_name_layout.setContentsMargins(0, 0, 0, 0)
        svc_name_layout.setSpacing(4)
        svc_name_label = QLabel("服务名称")
        svc_name_label.setStyleSheet("color: #666; font-size: 12px;")
        svc_name_layout.addWidget(svc_name_label)
        self.detail_fields = {}
        svc_name_edit = QLineEdit()
        svc_name_edit.setPlaceholderText("请输入服务名称")
        svc_name_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0099ff;
            }
        """)
        svc_name_layout.addWidget(svc_name_edit)
        self.detail_fields["service_name"] = svc_name_edit
        server_grid_layout.addWidget(svc_name_group, 1)

        # SSH主机IP
        ssh_host_group = QWidget()
        ssh_host_layout = QVBoxLayout(ssh_host_group)
        ssh_host_layout.setContentsMargins(0, 0, 0, 0)
        ssh_host_layout.setSpacing(4)
        ssh_host_label = QLabel("SSH主机IP")
        ssh_host_label.setStyleSheet("color: #666; font-size: 12px;")
        ssh_host_layout.addWidget(ssh_host_label)
        ssh_host_edit = QLineEdit()
        ssh_host_edit.setPlaceholderText("默认全局IP")
        ssh_host_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0099ff;
            }
        """)
        ssh_host_layout.addWidget(ssh_host_edit)
        self.detail_fields["ssh_host"] = ssh_host_edit
        server_grid_layout.addWidget(ssh_host_group, 1)

        # SSH登录用户名
        ssh_user_group = QWidget()
        ssh_user_layout = QVBoxLayout(ssh_user_group)
        ssh_user_layout.setContentsMargins(0, 0, 0, 0)
        ssh_user_layout.setSpacing(4)
        ssh_user_label = QLabel("SSH登录用户名")
        ssh_user_label.setStyleSheet("color: #666; font-size: 12px;")
        ssh_user_layout.addWidget(ssh_user_label)
        ssh_user_edit = QLineEdit()
        ssh_user_edit.setPlaceholderText("默认全局用户")
        ssh_user_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0099ff;
            }
        """)
        ssh_user_layout.addWidget(ssh_user_edit)
        self.detail_fields["ssh_host"] = ssh_host_edit
        self.detail_fields["ssh_user"] = ssh_user_edit
        server_grid_layout.addWidget(ssh_user_group, 1)

        detail_outer_layout.addWidget(server_grid)

        # 部署制品与容器设定标题
        deploy_title = QLabel("部署制品与容器设定")
        deploy_title.setStyleSheet("""
            font-weight: bold;
            font-size: 13px;
            color: #333;
            padding-left: 12px;
            border-left: 3px solid #0099ff;
            margin-top: 20px;
            margin-bottom: 12px;
        """)
        detail_outer_layout.addWidget(deploy_title)

        # 部署字段第一行
        deploy_row1 = QWidget()
        deploy_row1_layout = QHBoxLayout(deploy_row1)
        deploy_row1_layout.setContentsMargins(0, 0, 0, 0)
        deploy_row1_layout.setSpacing(20)

        # 本地Jar路径
        local_jar_group = QWidget()
        local_jar_layout = QVBoxLayout(local_jar_group)
        local_jar_layout.setContentsMargins(0, 0, 0, 0)
        local_jar_layout.setSpacing(4)
        local_jar_label = QLabel("本地制品包 (Jar) 路径")
        local_jar_label.setStyleSheet("color: #666; font-size: 12px;")
        local_jar_layout.addWidget(local_jar_label)
        local_jar_row = QHBoxLayout()
        local_jar_edit = QLineEdit()
        local_jar_edit.setPlaceholderText("浏览或输入路径")
        local_jar_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0099ff;
            }
        """)
        local_jar_row.addWidget(local_jar_edit)
        local_jar_browse = QPushButton("浏览...")
        local_jar_browse.setFixedWidth(70)
        local_jar_browse.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        local_jar_browse.clicked.connect(lambda checked, k="local_jar_path", e=local_jar_edit: self._browse_field(k, e))
        local_jar_row.addWidget(local_jar_browse)
        local_jar_layout.addLayout(local_jar_row)
        self.detail_fields["local_jar_path"] = local_jar_edit
        deploy_row1_layout.addWidget(local_jar_group, 2)

        # 服务器存储Jar绝对路径
        remote_jar_group = QWidget()
        remote_jar_layout = QVBoxLayout(remote_jar_group)
        remote_jar_layout.setContentsMargins(0, 0, 0, 0)
        remote_jar_layout.setSpacing(4)
        remote_jar_label = QLabel("服务器存储 Jar 绝对路径")
        remote_jar_label.setStyleSheet("color: #666; font-size: 12px;")
        remote_jar_layout.addWidget(remote_jar_label)
        remote_jar_edit = QLineEdit()
        remote_jar_edit.setPlaceholderText("/data/jar")
        remote_jar_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0099ff;
            }
        """)
        remote_jar_layout.addWidget(remote_jar_edit)
        self.detail_fields["remote_jar_dir"] = remote_jar_edit
        deploy_row1_layout.addWidget(remote_jar_group, 1)

        detail_outer_layout.addWidget(deploy_row1)

        # 部署字段第二行
        deploy_row2 = QWidget()
        deploy_row2_layout = QHBoxLayout(deploy_row2)
        deploy_row2_layout.setContentsMargins(0, 0, 0, 0)
        deploy_row2_layout.setSpacing(20)

        # Docker Compose运行目录
        compose_dir_group = QWidget()
        compose_dir_layout = QVBoxLayout(compose_dir_group)
        compose_dir_layout.setContentsMargins(0, 0, 0, 0)
        compose_dir_layout.setSpacing(4)
        compose_dir_label = QLabel("Docker Compose 运行目录")
        compose_dir_label.setStyleSheet("color: #666; font-size: 12px;")
        compose_dir_layout.addWidget(compose_dir_label)
        compose_dir_edit = QLineEdit()
        compose_dir_edit.setPlaceholderText("/data/app")
        compose_dir_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0099ff;
            }
        """)
        compose_dir_layout.addWidget(compose_dir_edit)
        self.detail_fields["compose_dir"] = compose_dir_edit
        deploy_row2_layout.addWidget(compose_dir_group, 1)

        # Docker Compose服务标识
        compose_svc_group = QWidget()
        compose_svc_layout = QVBoxLayout(compose_svc_group)
        compose_svc_layout.setContentsMargins(0, 0, 0, 0)
        compose_svc_layout.setSpacing(4)
        compose_svc_label = QLabel("Docker Compose 服务标识 (Service Name)")
        compose_svc_label.setStyleSheet("color: #666; font-size: 12px;")
        compose_svc_layout.addWidget(compose_svc_label)
        compose_svc_edit = QLineEdit()
        compose_svc_edit.setPlaceholderText("例如: contract")
        compose_svc_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0099ff;
            }
        """)
        compose_svc_layout.addWidget(compose_svc_edit)
        self.detail_fields["compose_service_name"] = compose_svc_edit
        deploy_row2_layout.addWidget(compose_svc_group, 1)

        detail_outer_layout.addWidget(deploy_row2)

        # 运行日志回传与备份配置标题
        log_config_title = QLabel("运行日志回传与备份配置")
        log_config_title.setStyleSheet("""
            font-weight: bold;
            font-size: 13px;
            color: #333;
            padding-left: 12px;
            border-left: 3px solid #0099ff;
            margin-top: 20px;
            margin-bottom: 12px;
        """)
        detail_outer_layout.addWidget(log_config_title)

        # 日志配置行
        log_config_row = QWidget()
        log_config_row_layout = QHBoxLayout(log_config_row)
        log_config_row_layout.setContentsMargins(0, 0, 0, 0)
        log_config_row_layout.setSpacing(20)

        # 服务端容器日志路径
        remote_log_group = QWidget()
        remote_log_layout = QVBoxLayout(remote_log_group)
        remote_log_layout.setContentsMargins(0, 0, 0, 0)
        remote_log_layout.setSpacing(4)
        remote_log_label = QLabel("服务端容器日志路径 (Remote Path)")
        remote_log_label.setStyleSheet("color: #666; font-size: 12px;")
        remote_log_layout.addWidget(remote_log_label)
        remote_log_edit = QLineEdit()
        remote_log_edit.setPlaceholderText("/data/logs/")
        remote_log_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0099ff;
            }
        """)
        remote_log_layout.addWidget(remote_log_edit)
        self.detail_fields["remote_log_path"] = remote_log_edit
        log_config_row_layout.addWidget(remote_log_group, 1)

        # 本地备份日志保存目录
        local_log_group = QWidget()
        local_log_layout = QVBoxLayout(local_log_group)
        local_log_layout.setContentsMargins(0, 0, 0, 0)
        local_log_layout.setSpacing(4)
        local_log_label = QLabel("本地备份日志保存目录 (Local Backup Path)")
        local_log_label.setStyleSheet("color: #666; font-size: 12px;")
        local_log_layout.addWidget(local_log_label)
        local_log_row = QHBoxLayout()
        local_log_edit = QLineEdit()
        local_log_edit.setPlaceholderText("浏览或输入路径")
        local_log_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0099ff;
            }
        """)
        local_log_row.addWidget(local_log_edit)
        local_log_browse = QPushButton("浏览...")
        local_log_browse.setFixedWidth(70)
        local_log_browse.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        local_log_browse.clicked.connect(lambda checked, k="local_log_dir", e=local_log_edit: self._browse_field(k, e))
        local_log_row.addWidget(local_log_browse)
        local_log_layout.addLayout(local_log_row)
        self.detail_fields["local_log_dir"] = local_log_edit
        log_config_row_layout.addWidget(local_log_group, 2)

        detail_outer_layout.addWidget(log_config_row)

        # 保存按钮
        save_btn_row = QHBoxLayout()
        save_btn_row.addStretch()
        save_detail_btn = QPushButton("保存配置修改")
        save_detail_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #0099ff;
            }
        """)
        save_detail_btn.clicked.connect(self._save_detail)
        save_btn_row.addWidget(save_detail_btn)
        detail_outer_layout.addLayout(save_btn_row)

        right_layout.addWidget(detail_container, 3)

        # 操作按钮区
        ops_container = QWidget()
        ops_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-top: 1px solid #e9ecef;
            }
        """)
        ops_layout = QHBoxLayout(ops_container)
        ops_layout.setContentsMargins(0, 16, 0, 16)
        ops_layout.setSpacing(12)

        self.upload_btn = QPushButton("↑ 上传 Jar 包")
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px 20px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #0099ff;
            }
        """)
        self.upload_btn.clicked.connect(self._do_upload)
        ops_layout.addWidget(self.upload_btn)

        self.restart_btn = QPushButton("⟳ 重启 Compose 容器")
        self.restart_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px 20px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #0099ff;
            }
        """)
        self.restart_btn.clicked.connect(self._do_restart)
        ops_layout.addWidget(self.restart_btn)

        self.download_btn = QPushButton("↓ 下载远程日志")
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px 20px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #0099ff;
            }
        """)
        self.download_btn.clicked.connect(self._do_download)
        ops_layout.addWidget(self.download_btn)

        self.archive_cb = QCheckBox("时间戳备份归档")
        self.archive_cb.setStyleSheet("font-weight: 500; padding: 0 8px;")
        ops_layout.addWidget(self.archive_cb)

        ops_layout.addStretch()

        self.oneclick_btn = QPushButton("⚙ 一键全部部署")
        self.oneclick_btn.setStyleSheet("""
            QPushButton {
                background-color: #0099ff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0080e6;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.oneclick_btn.clicked.connect(self._do_oneclick)
        ops_layout.addWidget(self.oneclick_btn)

        right_layout.addWidget(ops_container)

        # 日志区
        log_container = QWidget()
        log_container.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)

        log_header = QWidget()
        log_header.setStyleSheet("""
            QWidget {
                background-color: #2d3748;
                border-radius: 8px 8px 0 0;
            }
        """)
        log_header_layout = QHBoxLayout(log_header)
        log_header_layout.setContentsMargins(16, 12, 16, 12)

        log_title = QLabel("▶_ Deployment Log Shell")
        log_title.setStyleSheet("""
            color: #00ff88;
            font-family: Consolas, monospace;
            font-size: 13px;
            font-weight: bold;
        """)
        log_header_layout.addWidget(log_title)

        log_header_layout.addStretch()

        clear_btn = QPushButton("清空屏幕")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #e2e8f0;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6577;
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
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                border-radius: 0 0 8px 8px;
                padding: 12px;
            }
        """)
        log_layout.addWidget(self.log_text)

        right_layout.addWidget(log_container, 2)

        splitter.addWidget(right)
        splitter.setSizes([280, 720])

        # 状态栏
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #f8f9fa;
                border-top: 1px solid #e9ecef;
                padding: 4px 12px;
                color: #666;
            }
        """)
        self.statusBar().showMessage("就绪")

    def _init_menu(self):
        menu_bar = self.menuBar()

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

        toolbox_action = QAction("🧰 工具箱", self)
        toolbox_action.triggered.connect(self._open_toolbox)
        tools_menu.addAction(toolbox_action)

        tools_menu.addSeparator()

        json_formatter_action = QAction("JSON 格式化", self)
        json_formatter_action.triggered.connect(self._open_json_formatter)
        tools_menu.addAction(json_formatter_action)

        port_manager_action = QAction("端口管理", self)
        port_manager_action.triggered.connect(self._open_port_manager)
        tools_menu.addAction(port_manager_action)

        sql_generator_action = QAction("SQL 生成器", self)
        sql_generator_action.triggered.connect(self._open_sql_generator)
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

    def _open_json_formatter(self):
        """打开 JSON 格式化工具"""
        dlg = JsonFormatterDialog(self)
        dlg.exec()

    def _open_port_manager(self):
        """打开端口管理工具"""
        dlg = PortManagerDialog(self)
        dlg.exec()

    def _open_sql_generator(self):
        """打开 SQL 生成器"""
        dlg = SqlGeneratorDialog(self)
        dlg.exec()

    def _open_toolbox(self):
        """打开工具箱"""
        dlg = ToolboxDialog(self)
        dlg.exec()
