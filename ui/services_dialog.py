from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QFileDialog, QMessageBox, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt


class ServiceEditDialog(QDialog):
    LABELS = {
        "service_name": "服务名称",
        "ssh_host": "SSH主机",
        "ssh_user": "SSH用户",
        "local_jar_path": "本地Jar路径",
        "remote_jar_dir": "远程Jar目录",
        "compose_dir": "Compose目录",
        "compose_service_name": "Compose服务名",
        "remote_log_path": "远程日志路径",
        "local_log_dir": "本地日志目录",
    }
    FIELDS = [
        "service_name", "ssh_host", "ssh_user", "local_jar_path",
        "remote_jar_dir", "compose_dir", "compose_service_name",
        "remote_log_path", "local_log_dir"
    ]

    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.data = data or {}
        self.setWindowTitle("编辑服务" if data else "新增服务")
        self.setMinimumWidth(500)
        self._init_ui()

    def _init_ui(self):
        from PySide6.QtWidgets import QFormLayout, QLineEdit
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.edits = {}

        for field in self.FIELDS:
            edit = QLineEdit(self.data.get(field, ""))
            if field in ("local_jar_path", "local_log_dir"):
                row = QHBoxLayout()
                row.addWidget(edit)
                btn = QPushButton("浏览...")
                btn.clicked.connect(lambda checked, f=field, e=edit: self._browse(f, e))
                row.addWidget(btn)
                form.addRow(self.LABELS[field] + ":", row)
            else:
                form.addRow(self.LABELS[field] + ":", edit)
            self.edits[field] = edit

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _browse(self, field, edit):
        if field == "local_jar_path":
            path, _ = QFileDialog.getOpenFileName(self, "选择Jar文件", "", "Jar文件 (*.jar);;所有文件 (*)")
        else:
            path = QFileDialog.getExistingDirectory(self, "选择目录")
        if path:
            edit.setText(path)

    def get_data(self):
        return {f: self.edits[f].text().strip() for f in self.FIELDS}


class ServicesDialog(QDialog):
    HEADERS = ["服务名称", "SSH主机", "SSH用户", "本地Jar路径", "远程Jar目录",
               "Compose目录", "Compose服务名", "远程日志路径", "本地日志目录"]
    FIELDS = [
        "service_name", "ssh_host", "ssh_user", "local_jar_path",
        "remote_jar_dir", "compose_dir", "compose_service_name",
        "remote_log_path", "local_log_dir"
    ]

    def __init__(self, services, parent=None):
        super().__init__(parent)
        self.services = [s.copy() for s in services]
        self.setWindowTitle("服务管理")
        self.setMinimumSize(900, 400)
        self._init_ui()
        self._refresh_table()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.doubleClicked.connect(self._edit_service)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("新增")
        add_btn.clicked.connect(self._add_service)
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self._edit_service)
        del_btn = QPushButton("删除")
        del_btn.clicked.connect(self._delete_service)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()

        save_btn = QPushButton("保存并关闭")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _refresh_table(self):
        self.table.setRowCount(len(self.services))
        for row, svc in enumerate(self.services):
            for col, field in enumerate(self.FIELDS):
                item = QTableWidgetItem(svc.get(field, ""))
                self.table.setItem(row, col, item)

    def _add_service(self):
        dlg = ServiceEditDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.services.append(dlg.get_data())
            self._refresh_table()

    def _edit_service(self):
        row = self.table.currentRow()
        if row < 0:
            return
        dlg = ServiceEditDialog(self.services[row], parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.services[row] = dlg.get_data()
            self._refresh_table()

    def _delete_service(self):
        row = self.table.currentRow()
        if row < 0:
            return
        name = self.services[row].get("service_name", "")
        if QMessageBox.question(self, "确认删除", f"确定要删除服务 \"{name}\" 吗？") == QMessageBox.Yes:
            self.services.pop(row)
            self._refresh_table()

    def get_services(self):
        return self.services
