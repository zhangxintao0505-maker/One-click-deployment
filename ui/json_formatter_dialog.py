"""JSON 格式化工具对话框"""
import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QMessageBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter


class JsonHighlighter(QSyntaxHighlighter):
    """JSON 语法高亮"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # 键（key）
        key_format = QTextCharFormat()
        key_format.setForeground(QColor("#0451a5"))
        key_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'"[^"]*"(?=\s*:)', key_format))

        # 字符串值
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#a31515"))
        self.highlighting_rules.append((r'"[^"]*"', string_format))

        # 数字
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#098658"))
        self.highlighting_rules.append((r'\b\d+\.?\d*\b', number_format))

        # 布尔值和null
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#0000ff"))
        self.highlighting_rules.append((r'\b(true|false|null)\b', keyword_format))

    def highlightBlock(self, text):
        import re
        for pattern, fmt in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, fmt)


class JsonFormatterDialog(QDialog):
    """JSON 格式化工具对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JSON 格式化工具")
        self.setMinimumSize(700, 500)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 标题
        title = QLabel("JSON 格式化工具")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333;
            padding: 8px 0;
            border-left: 3px solid #0099ff;
            padding-left: 12px;
        """)
        layout.addWidget(title)

        # 输入区标签
        input_label = QLabel("输入 JSON 数据：")
        input_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(input_label)

        # 输入区
        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("请粘贴或输入 JSON 数据...")
        self.input_edit.setFont(QFont("Consolas", 11))
        self.input_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px;
                background-color: #fafafa;
            }
            QTextEdit:focus {
                border-color: #0099ff;
            }
        """)
        layout.addWidget(self.input_edit)

        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        # 格式化按钮
        format_btn = QPushButton("✨ 格式化")
        format_btn.setStyleSheet("""
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
        format_btn.clicked.connect(self._format_json)
        btn_layout.addWidget(format_btn)

        # 压缩按钮
        compress_btn = QPushButton("📦 压缩")
        compress_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        compress_btn.clicked.connect(self._compress_json)
        btn_layout.addWidget(compress_btn)

        # 验证按钮
        validate_btn = QPushButton("✓ 验证")
        validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        validate_btn.clicked.connect(self._validate_json)
        btn_layout.addWidget(validate_btn)

        # 清空按钮
        clear_btn = QPushButton("🗑 清空")
        clear_btn.setStyleSheet("""
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
        clear_btn.clicked.connect(self._clear_all)
        btn_layout.addWidget(clear_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 输出区标签
        output_label = QLabel("格式化结果：")
        output_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(output_label)

        # 输出区
        self.output_edit = QTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setFont(QFont("Consolas", 11))
        self.output_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px;
                background-color: #fff;
            }
        """)
        # 添加语法高亮
        self.highlighter = JsonHighlighter(self.output_edit.document())
        layout.addWidget(self.output_edit)

        # 底部按钮
        bottom_layout = QHBoxLayout()

        # 复制按钮
        copy_btn = QPushButton("📋 复制结果")
        copy_btn.setStyleSheet("""
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
        copy_btn.clicked.connect(self._copy_result)
        bottom_layout.addWidget(copy_btn)

        bottom_layout.addStretch()

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
        bottom_layout.addWidget(close_btn)

        layout.addLayout(bottom_layout)

    def _format_json(self):
        """格式化 JSON"""
        text = self.input_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入 JSON 数据")
            return

        try:
            data = json.loads(text)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            self.output_edit.setPlainText(formatted)
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "JSON 格式错误", f"解析失败:\n{str(e)}")

    def _compress_json(self):
        """压缩 JSON"""
        text = self.input_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入 JSON 数据")
            return

        try:
            data = json.loads(text)
            compressed = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            self.output_edit.setPlainText(compressed)
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "JSON 格式错误", f"解析失败:\n{str(e)}")

    def _validate_json(self):
        """验证 JSON"""
        text = self.input_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入 JSON 数据")
            return

        try:
            json.loads(text)
            QMessageBox.information(self, "验证通过", "✓ JSON 格式正确！")
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "验证失败", f"JSON 格式错误:\n{str(e)}")

    def _clear_all(self):
        """清空输入输出"""
        self.input_edit.clear()
        self.output_edit.clear()

    def _copy_result(self):
        """复制结果到剪贴板"""
        text = self.output_edit.toPlainText()
        if text:
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "复制成功", "结果已复制到剪贴板")
        else:
            QMessageBox.warning(self, "提示", "没有可复制的内容")
