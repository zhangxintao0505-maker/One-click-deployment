from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QPushButton, QHBoxLayout, QFileDialog, QMessageBox, QWidget, QLabel
)
from PySide6.QtCore import Qt


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.setWindowTitle("全局设置")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self._init_ui()

    def _init_ui(self):
        # 设置对话框样式
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # 标题
        title = QLabel("全局设置")
        title.setStyleSheet("""
            font-weight: bold;
            font-size: 16px;
            color: #333;
            border-left: 3px solid #0099ff;
            padding-left: 12px;
            margin-bottom: 8px;
        """)
        layout.addWidget(title)

        # 描述文字
        desc = QLabel("配置SSH连接的全局默认参数，服务级配置会覆盖这些值。")
        desc.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 12px;")
        layout.addWidget(desc)

        # SSH连接配置
        form = QFormLayout()
        form.setSpacing(16)

        # 默认主机
        self.host_edit = QLineEdit(self.config.get("default_ssh_host", ""))
        self.host_edit.setPlaceholderText("例如: 192.168.1.100")
        self.host_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0099ff;
            }
        """)
        form.addRow("默认主机:", self.host_edit)

        # 默认用户
        self.user_edit = QLineEdit(self.config.get("default_ssh_user", ""))
        self.user_edit.setPlaceholderText("例如: root")
        self.user_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0099ff;
            }
        """)
        form.addRow("默认用户:", self.user_edit)

        # 默认端口
        self.port_edit = QLineEdit(str(self.config.get("default_ssh_port", 22)))
        self.port_edit.setPlaceholderText("默认: 22")
        self.port_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0099ff;
            }
        """)
        form.addRow("默认端口:", self.port_edit)

        # 认证方式
        self.auth_combo = QComboBox()
        self.auth_combo.addItems(["key", "password"])
        self.auth_combo.setCurrentText(self.config.get("auth_method", "key"))
        self.auth_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
                background-color: white;
            }
            QComboBox:focus {
                border-color: #0099ff;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            QComboBox::down-arrow {
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
            }
        """)
        form.addRow("认证方式:", self.auth_combo)

        # 私钥路径
        key_widget = QWidget()
        key_layout = QHBoxLayout(key_widget)
        key_layout.setContentsMargins(0, 0, 0, 0)
        key_layout.setSpacing(8)
        self.key_edit = QLineEdit(self.config.get("ssh_key_path", ""))
        self.key_edit.setPlaceholderText("浏览选择SSH私钥文件")
        self.key_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0099ff;
            }
        """)
        key_layout.addWidget(self.key_edit)
        key_btn = QPushButton("浏览...")
        key_btn.setFixedWidth(80)
        key_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        key_btn.clicked.connect(self._browse_key)
        key_layout.addWidget(key_btn)
        form.addRow("私钥路径:", key_widget)

        # 密码
        self.password_edit = QLineEdit(self.config.get("ssh_password", ""))
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("输入SSH密码")
        self.password_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0099ff;
            }
        """)
        form.addRow("密码:", self.password_edit)

        layout.addLayout(form)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        # 保存按钮
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet("""
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
        """)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #0099ff;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _browse_key(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择SSH私钥文件")
        if path:
            self.key_edit.setText(path)

    def get_config(self):
        return {
            "default_ssh_host": self.host_edit.text().strip(),
            "default_ssh_user": self.user_edit.text().strip(),
            "default_ssh_port": int(self.port_edit.text().strip() or 22),
            "auth_method": self.auth_combo.currentText(),
            "ssh_key_path": self.key_edit.text().strip(),
            "ssh_password": self.password_edit.text(),
        }
