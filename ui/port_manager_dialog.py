"""端口管理工具对话框"""
import json
import subprocess
import platform
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QMessageBox, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont


class PortCheckWorker(QThread):
    """端口检测工作线程"""
    finished = Signal(str)  # results_json: {port: {pid, name, status}}

    def __init__(self, ports):
        super().__init__()
        self.ports = ports

    def run(self):
        results = {}
        for port in self.ports:
            result = self._check_port(port)
            results[port] = result
        self.finished.emit(json.dumps(results))

    def _check_port(self, port):
        """检测端口占用"""
        try:
            if platform.system() == "Windows":
                # Windows: 使用 netstat 命令
                cmd = f'netstat -ano | findstr ":{port} "'
                output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
                lines = output.strip().split('\n')
                for line in lines:
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        pid = parts[-1]
                        # 获取进程名称
                        try:
                            tasklist = subprocess.check_output(
                                f'tasklist /FI "PID eq {pid}" /FO CSV /NH',
                                shell=True, text=True, stderr=subprocess.DEVNULL
                            )
                            name = tasklist.split(',')[0].strip('"')
                        except:
                            name = "未知"
                        return {"pid": pid, "name": name, "status": "占用"}
                return {"pid": "-", "name": "-", "status": "空闲"}
            else:
                # Linux/Mac: 使用 lsof 或 ss
                cmd = f'ss -tlnp | grep ":{port}"'
                output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
                if output.strip():
                    return {"pid": "-", "name": "-", "status": "占用"}
                return {"pid": "-", "name": "-", "status": "空闲"}
        except subprocess.CalledProcessError:
            return {"pid": "-", "name": "-", "status": "空闲"}
        except Exception as e:
            return {"pid": "-", "name": "-", "status": f"检测失败: {str(e)}"}


class PortManagerDialog(QDialog):
    """端口管理工具对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("端口管理工具")
        self.setMinimumSize(650, 500)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 标题
        title = QLabel("端口管理工具")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333;
            padding: 8px 0;
            border-left: 3px solid #0099ff;
            padding-left: 12px;
        """)
        layout.addWidget(title)

        # 输入区
        input_group = QGroupBox("端口检测")
        input_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        input_layout = QVBoxLayout(input_group)

        input_hint = QLabel("输入端口号（多个端口用逗号分隔，如: 8080,3306,6379）")
        input_hint.setStyleSheet("color: #666; font-size: 12px; font-weight: normal;")
        input_layout.addWidget(input_hint)

        port_input_layout = QHBoxLayout()
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("请输入端口号...")
        self.port_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0099ff;
            }
        """)
        self.port_input.returnPressed.connect(self._check_ports)
        port_input_layout.addWidget(self.port_input)

        check_btn = QPushButton("🔍 检测")
        check_btn.setStyleSheet("""
            QPushButton {
                background-color: #0099ff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0080e6;
            }
        """)
        check_btn.clicked.connect(self._check_ports)
        port_input_layout.addWidget(check_btn)

        input_layout.addLayout(port_input_layout)
        layout.addWidget(input_group)

        # 结果表格
        result_group = QGroupBox("检测结果")
        result_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        result_layout = QVBoxLayout(result_group)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["端口", "状态", "进程ID", "进程名称"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.result_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.result_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                gridline-color: #e9ecef;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                border: none;
                border-bottom: 1px solid #dee2e6;
                padding: 8px;
                font-weight: bold;
            }
        """)
        result_layout.addWidget(self.result_table)
        layout.addWidget(result_group)

        # 操作按钮
        btn_layout = QHBoxLayout()

        # 释放端口按钮
        release_btn = QPushButton("🔥 释放选中端口")
        release_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        release_btn.clicked.connect(self._release_port)
        btn_layout.addWidget(release_btn)

        btn_layout.addStretch()

        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        refresh_btn.clicked.connect(self._check_ports)
        btn_layout.addWidget(refresh_btn)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
        """)
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        self.worker = None

    def _check_ports(self):
        """检测端口"""
        text = self.port_input.text().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入端口号")
            return

        try:
            ports = [int(p.strip()) for p in text.split(',') if p.strip()]
        except ValueError:
            QMessageBox.warning(self, "提示", "端口号必须是数字")
            return

        self.result_table.setRowCount(0)
        self.result_table.setRowCount(len(ports))
        for i, port in enumerate(ports):
            item = QTableWidgetItem(str(port))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.result_table.setItem(i, 0, item)
            status_item = QTableWidgetItem("检测中...")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.result_table.setItem(i, 1, status_item)

        self.worker = PortCheckWorker(ports)
        self.worker.finished.connect(self._on_check_finished)
        self.worker.start()

    def _on_check_finished(self, results_json):
        """检测完成"""
        results = json.loads(results_json)
        for i, (port, info) in enumerate(results.items()):
            # 状态
            status_item = QTableWidgetItem(info["status"])
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if info["status"] == "占用":
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.green)
            self.result_table.setItem(i, 1, status_item)

            # PID
            pid_item = QTableWidgetItem(info["pid"])
            pid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.result_table.setItem(i, 2, pid_item)

            # 进程名称
            name_item = QTableWidgetItem(info["name"])
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.result_table.setItem(i, 3, name_item)

    def _release_port(self):
        """释放端口"""
        row = self.result_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择要释放的端口")
            return

        port_item = self.result_table.item(row, 0)
        status_item = self.result_table.item(row, 1)
        pid_item = self.result_table.item(row, 2)

        if not port_item:
            return

        port = port_item.text()
        status = status_item.text() if status_item else ""
        pid = pid_item.text() if pid_item else "-"

        if status != "占用":
            QMessageBox.information(self, "提示", f"端口 {port} 未被占用")
            return

        reply = QMessageBox.question(
            self, "确认释放",
            f"确定要释放端口 {port} 吗？\n\n"
            f"进程ID: {pid}\n\n"
            "这将强制结束该进程！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if platform.system() == "Windows":
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True, check=True)
                else:
                    subprocess.run(f'kill -9 {pid}', shell=True, check=True)
                QMessageBox.information(self, "成功", f"端口 {port} 已释放")
                self._check_ports()
            except subprocess.CalledProcessError:
                QMessageBox.warning(self, "失败", f"无法释放端口 {port}\n可能需要管理员权限")
