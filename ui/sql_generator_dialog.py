"""数据库连接与 SQL 生成器对话框 - AI + 可视化双模式"""
import json
import os
import subprocess
import platform
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QMessageBox, QLineEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QWidget, QFormLayout, QTabWidget,
    QListWidget, QListWidgetItem, QSplitter, QCheckBox,
    QSpinBox, QFileDialog, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QColor, QIcon, QDrag, QCursor


class DatabaseConnectWorker(QThread):
    """数据库连接工作线程"""
    finished = Signal(bool, str, str)

    def __init__(self, config, db_type):
        super().__init__()
        self.config = config
        self.db_type = db_type

    def run(self):
        try:
            if self.db_type == "MySQL":
                import pymysql
                conn = pymysql.connect(
                    host=self.config["host"],
                    port=int(self.config["port"]),
                    user=self.config["user"],
                    password=self.config["password"],
                    database=self.config["database"],
                    charset='utf8mb4'
                )
                cursor = conn.cursor()
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
                conn.close()
                self.finished.emit(True, "连接成功", json.dumps(tables))
            elif self.db_type == "PostgreSQL":
                import psycopg2
                conn = psycopg2.connect(
                    host=self.config["host"],
                    port=int(self.config["port"]),
                    user=self.config["user"],
                    password=self.config["password"],
                    dbname=self.config["database"]
                )
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                conn.close()
                self.finished.emit(True, "连接成功", json.dumps(tables))
        except ImportError as e:
            self.finished.emit(False, f"缺少数据库驱动: {str(e)}\n请安装: pip install pymysql psycopg2-binary", "[]")
        except Exception as e:
            self.finished.emit(False, f"连接失败: {str(e)}", "[]")


class TableSchemaWorker(QThread):
    """获取表结构工作线程"""
    finished = Signal(bool, str, str)

    def __init__(self, config, db_type, table_name):
        super().__init__()
        self.config = config
        self.db_type = db_type
        self.table_name = table_name

    def run(self):
        try:
            if self.db_type == "MySQL":
                import pymysql
                conn = pymysql.connect(
                    host=self.config["host"],
                    port=int(self.config["port"]),
                    user=self.config["user"],
                    password=self.config["password"],
                    database=self.config["database"],
                    charset='utf8mb4'
                )
                cursor = conn.cursor()
                cursor.execute(f"DESCRIBE `{self.table_name}`")
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        "name": row[0],
                        "type": row[1],
                        "key": row[2],
                        "default": row[4]
                    })
                # 获取外键关系
                cursor.execute(f"""
                    SELECT
                        COLUMN_NAME,
                        REFERENCED_TABLE_NAME,
                        REFERENCED_COLUMN_NAME
                    FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_NAME = '{self.table_name}'
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """)
                foreign_keys = {}
                for row in cursor.fetchall():
                    foreign_keys[row[0]] = {
                        "table": row[1],
                        "column": row[2]
                    }
                conn.close()
                self.finished.emit(True, "获取成功", json.dumps({
                    "columns": columns,
                    "foreign_keys": foreign_keys
                }))
            elif self.db_type == "PostgreSQL":
                import psycopg2
                conn = psycopg2.connect(
                    host=self.config["host"],
                    port=int(self.config["port"]),
                    user=self.config["user"],
                    password=self.config["password"],
                    dbname=self.config["database"]
                )
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_name = '{self.table_name}'
                    ORDER BY ordinal_position
                """)
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        "name": row[0],
                        "type": row[1],
                        "key": "PRI" if row[0] == "id" else "",
                        "default": row[3]
                    })
                # 获取外键关系
                cursor.execute(f"""
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS referenced_table,
                        ccu.column_name AS referenced_column
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu
                        ON tc.constraint_name = ccu.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name = '{self.table_name}'
                """)
                foreign_keys = {}
                for row in cursor.fetchall():
                    foreign_keys[row[0]] = {
                        "table": row[1],
                        "column": row[2]
                    }
                conn.close()
                self.finished.emit(True, "获取成功", json.dumps({
                    "columns": columns,
                    "foreign_keys": foreign_keys
                }))
        except Exception as e:
            self.finished.emit(False, f"获取失败: {str(e)}", "{}")


class SqlGeneratorDialog(QDialog):
    """数据库连接与 SQL 生成器对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SQL 生成器")
        self.setMinimumSize(950, 700)
        self.tables = []
        self.table_schemas = {}
        self.current_config = {}
        self.ai_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 标题
        title = QLabel("数据库 SQL 生成器")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333;
            padding: 8px 0;
            border-left: 3px solid #0099ff;
            padding-left: 12px;
        """)
        layout.addWidget(title)

        # 使用 Tab 页
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                margin-right: 4px;
                border: 1px solid #dee2e6;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                background-color: #f8f9fa;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #0099ff;
                font-weight: bold;
            }
        """)

        # Tab 1: 连接配置
        conn_tab = self._create_connection_tab()
        tabs.addTab(conn_tab, "连接配置")

        # Tab 2: AI SQL 生成
        ai_tab = self._create_ai_tab()
        tabs.addTab(ai_tab, "AI 生成")

        # Tab 3: 可视化构建
        visual_tab = self._create_visual_tab()
        tabs.addTab(visual_tab, "可视化构建")

        layout.addWidget(tabs)

        # 底部关闭按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
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

        self.connect_worker = None
        self.schema_worker = None

    def _create_connection_tab(self):
        """创建连接配置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 连接配置组
        conn_group = QGroupBox("数据库连接配置")
        conn_group.setStyleSheet("""
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
        conn_form = QFormLayout(conn_group)
        conn_form.setSpacing(12)

        style = """
            QLineEdit, QComboBox {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 12px;
                min-width: 200px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #0099ff;
            }
        """

        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(["MySQL", "PostgreSQL"])
        self.db_type_combo.setStyleSheet(style)
        conn_form.addRow("数据库类型:", self.db_type_combo)

        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("localhost")
        self.host_edit.setStyleSheet(style)
        conn_form.addRow("主机:", self.host_edit)

        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("3306")
        self.port_edit.setStyleSheet(style)
        conn_form.addRow("端口:", self.port_edit)

        self.database_edit = QLineEdit()
        self.database_edit.setPlaceholderText("请输入数据库名")
        self.database_edit.setStyleSheet(style)
        conn_form.addRow("数据库名:", self.database_edit)

        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("root")
        self.user_edit.setStyleSheet(style)
        conn_form.addRow("用户名:", self.user_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setStyleSheet(style)
        conn_form.addRow("密码:", self.password_edit)

        layout.addWidget(conn_group)

        # 连接按钮
        conn_btn_layout = QHBoxLayout()
        conn_btn_layout.addStretch()
        self.connect_btn = QPushButton("🔌 连接数据库")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #0099ff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0080e6;
            }
        """)
        self.connect_btn.clicked.connect(self._connect_database)
        conn_btn_layout.addWidget(self.connect_btn)
        layout.addLayout(conn_btn_layout)

        # 表列表
        table_group = QGroupBox("数据库表")
        table_group.setStyleSheet("""
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
        table_layout = QVBoxLayout(table_group)

        self.table_list = QListWidget()
        self.table_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        self.table_list.itemDoubleClicked.connect(self._on_table_double_clicked)
        table_layout.addWidget(self.table_list)

        layout.addWidget(table_group)
        return tab

    def _create_ai_tab(self):
        """创建 AI SQL 生成标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # API 配置
        api_group = QGroupBox("AI 配置")
        api_group.setStyleSheet("""
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
        api_layout = QHBoxLayout(api_group)

        api_key_label = QLabel("API Key:")
        api_key_label.setStyleSheet("color: #666;")
        api_layout.addWidget(api_key_label)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("输入 Claude API Key (sk-ant-...)")
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setText(self.ai_api_key)
        self.api_key_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px 12px;
            }
            QLineEdit:focus {
                border-color: #0099ff;
            }
        """)
        api_layout.addWidget(self.api_key_edit)

        save_key_btn = QPushButton("保存 Key")
        save_key_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        save_key_btn.clicked.connect(self._save_api_key)
        api_layout.addWidget(save_key_btn)

        layout.addWidget(api_group)

        # 左右分栏
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：需求输入
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        request_label = QLabel("输入查询需求（自然语言）：")
        request_label.setStyleSheet("font-weight: bold; color: #333; padding: 8px 0;")
        left_layout.addWidget(request_label)

        hint_label = QLabel("示例：\n"
                           "• 查询所有用户及其订单数量\n"
                           "• 找出销售额最高的前10个产品\n"
                           "• 统计每个部门的平均工资\n"
                           "• 查询没有下单的用户")
        hint_label.setStyleSheet("color: #666; font-size: 11px; padding: 4px; background-color: #f8f9fa; border-radius: 4px;")
        hint_label.setWordWrap(True)
        left_layout.addWidget(hint_label)

        self.ai_request_edit = QTextEdit()
        self.ai_request_edit.setPlaceholderText("请描述您想要查询的数据...")
        self.ai_request_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 12px;
                font-size: 13px;
            }
            QTextEdit:focus {
                border-color: #0099ff;
            }
        """)
        left_layout.addWidget(self.ai_request_edit)

        # 生成按钮
        gen_btn_layout = QHBoxLayout()
        self.ai_gen_btn = QPushButton("⚡ AI 生成 SQL")
        self.ai_gen_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.ai_gen_btn.clicked.connect(self._generate_sql_with_ai)
        gen_btn_layout.addWidget(self.ai_gen_btn)
        gen_btn_layout.addStretch()
        left_layout.addLayout(gen_btn_layout)

        splitter.addWidget(left_widget)

        # 右侧：SQL 输出
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        output_label = QLabel("AI 生成的 SQL：")
        output_label.setStyleSheet("font-weight: bold; color: #333; padding: 8px 0;")
        right_layout.addWidget(output_label)

        self.ai_sql_output = QTextEdit()
        self.ai_sql_output.setReadOnly(True)
        self.ai_sql_output.setFont(QFont("Consolas", 11))
        self.ai_sql_output.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 12px;
                background-color: #fafafa;
            }
        """)
        right_layout.addWidget(self.ai_sql_output)

        # 操作按钮
        ai_btn_layout = QHBoxLayout()

        copy_btn = QPushButton("📋 复制")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        copy_btn.clicked.connect(self._copy_ai_sql)
        ai_btn_layout.addWidget(copy_btn)

        export_btn = QPushButton("💾 导出")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        export_btn.clicked.connect(self._export_sql)
        ai_btn_layout.addWidget(export_btn)

        ai_btn_layout.addStretch()
        right_layout.addLayout(ai_btn_layout)

        splitter.addWidget(right_widget)
        splitter.setSizes([400, 500])

        layout.addWidget(splitter)
        return tab

    def _create_visual_tab(self):
        """创建可视化构建标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 主分栏
        main_splitter = QSplitter(Qt.Horizontal)

        # 左侧：表和字段选择
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 可用表
        tables_label = QLabel("可用表（双击添加）：")
        tables_label.setStyleSheet("font-weight: bold; color: #333; padding: 4px 0;")
        left_layout.addWidget(tables_label)

        self.visual_table_list = QListWidget()
        self.visual_table_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px;
                max-height: 150px;
            }
            QListWidget::item {
                padding: 6px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        self.visual_table_list.itemDoubleClicked.connect(self._add_table_to_query)
        left_layout.addWidget(self.visual_table_list)

        # 已选字段
        fields_label = QLabel("已选字段：")
        fields_label.setStyleSheet("font-weight: bold; color: #333; padding: 4px 0;")
        left_layout.addWidget(fields_label)

        self.selected_fields_list = QListWidget()
        self.selected_fields_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px;
                min-height: 120px;
            }
            QListWidget::item {
                padding: 6px;
                background-color: #e8f5e9;
                border-radius: 4px;
                margin: 2px;
            }
        """)
        left_layout.addWidget(self.selected_fields_list)

        # 移除字段按钮
        remove_field_btn = QPushButton("移除选中字段")
        remove_field_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        remove_field_btn.clicked.connect(self._remove_selected_field)
        left_layout.addWidget(remove_field_btn)

        main_splitter.addWidget(left_widget)

        # 中间：查询条件
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)

        # JOIN 条件
        join_group = QGroupBox("JOIN 条件")
        join_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        join_layout = QVBoxLayout(join_group)

        self.join_list = QListWidget()
        self.join_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px;
                min-height: 80px;
            }
            QListWidget::item {
                padding: 6px;
            }
        """)
        join_layout.addWidget(self.join_list)

        # 添加 JOIN
        add_join_layout = QHBoxLayout()
        self.join_table_combo = QComboBox()
        self.join_table_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        add_join_layout.addWidget(self.join_table_combo)

        self.join_type_combo = QComboBox()
        self.join_type_combo.addItems(["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN"])
        self.join_type_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        add_join_layout.addWidget(self.join_type_combo)

        add_join_btn = QPushButton("+")
        add_join_btn.setFixedSize(30, 30)
        add_join_btn.setStyleSheet("""
            QPushButton {
                background-color: #0099ff;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        add_join_btn.clicked.connect(self._add_join_condition)
        add_join_layout.addWidget(add_join_btn)

        join_layout.addLayout(add_join_layout)
        middle_layout.addWidget(join_group)

        # WHERE 条件
        where_group = QGroupBox("WHERE 条件")
        where_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        where_layout = QVBoxLayout(where_group)

        self.where_list = QListWidget()
        self.where_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px;
                min-height: 80px;
            }
            QListWidget::item {
                padding: 6px;
            }
        """)
        where_layout.addWidget(self.where_list)

        # 添加 WHERE
        add_where_layout = QHBoxLayout()
        self.where_field_combo = QComboBox()
        self.where_field_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        add_where_layout.addWidget(self.where_field_combo)

        self.where_op_combo = QComboBox()
        self.where_op_combo.addItems(["=", "!=", ">", "<", ">=", "<=", "LIKE", "IN", "IS NULL", "IS NOT NULL"])
        self.where_op_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
                min-width: 80px;
            }
        """)
        add_where_layout.addWidget(self.where_op_combo)

        self.where_value_edit = QLineEdit()
        self.where_value_edit.setPlaceholderText("值")
        self.where_value_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        add_where_layout.addWidget(self.where_value_edit)

        add_where_btn = QPushButton("+")
        add_where_btn.setFixedSize(30, 30)
        add_where_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        add_where_btn.clicked.connect(self._add_where_condition)
        add_where_layout.addWidget(add_where_btn)

        where_layout.addLayout(add_where_layout)
        middle_layout.addWidget(where_group)

        # GROUP BY / ORDER BY
        other_group = QGroupBox("分组与排序")
        other_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        other_layout = QFormLayout(other_group)

        self.group_by_combo = QComboBox()
        self.group_by_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        other_layout.addRow("GROUP BY:", self.group_by_combo)

        self.order_by_combo = QComboBox()
        self.order_by_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        other_layout.addRow("ORDER BY:", self.order_by_combo)

        self.order_dir_combo = QComboBox()
        self.order_dir_combo.addItems(["ASC", "DESC"])
        self.order_dir_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        other_layout.addRow("排序方向:", self.order_dir_combo)

        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(0, 100000)
        self.limit_spin.setValue(100)
        self.limit_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        other_layout.addRow("LIMIT:", self.limit_spin)

        middle_layout.addWidget(other_group)

        # 生成按钮
        visual_gen_layout = QHBoxLayout()
        visual_gen_layout.addStretch()
        visual_gen_btn = QPushButton("⚡ 生成 SQL")
        visual_gen_btn.setStyleSheet("""
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
        visual_gen_btn.clicked.connect(self._generate_visual_sql)
        visual_gen_layout.addWidget(visual_gen_btn)
        middle_layout.addLayout(visual_gen_layout)

        main_splitter.addWidget(middle_widget)

        # 右侧：SQL 输出
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        output_label = QLabel("生成的 SQL：")
        output_label.setStyleSheet("font-weight: bold; color: #333; padding: 4px 0;")
        right_layout.addWidget(output_label)

        self.visual_sql_output = QTextEdit()
        self.visual_sql_output.setReadOnly(True)
        self.visual_sql_output.setFont(QFont("Consolas", 11))
        self.visual_sql_output.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 12px;
                background-color: #fafafa;
            }
        """)
        right_layout.addWidget(self.visual_sql_output)

        # 操作按钮
        visual_btn_layout = QHBoxLayout()

        copy_visual_btn = QPushButton("📋 复制")
        copy_visual_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        copy_visual_btn.clicked.connect(self._copy_visual_sql)
        visual_btn_layout.addWidget(copy_visual_btn)

        export_visual_btn = QPushButton("💾 导出")
        export_visual_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        export_visual_btn.clicked.connect(self._export_sql)
        visual_btn_layout.addWidget(export_visual_btn)

        visual_btn_layout.addStretch()
        right_layout.addLayout(visual_btn_layout)

        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([250, 350, 300])

        layout.addWidget(main_splitter)

        # 查询状态
        self.query_state = {
            "tables": [],
            "fields": [],
            "joins": [],
            "where": [],
            "group_by": "",
            "order_by": "",
            "order_dir": "ASC",
            "limit": 100
        }

        return tab

    def _connect_database(self):
        """连接数据库"""
        self.current_config = {
            "host": self.host_edit.text().strip() or "localhost",
            "port": self.port_edit.text().strip() or "3306",
            "user": self.user_edit.text().strip() or "root",
            "password": self.password_edit.text(),
            "database": self.database_edit.text().strip()
        }

        if not self.current_config["database"]:
            QMessageBox.warning(self, "提示", "请输入数据库名")
            return

        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("连接中...")

        self.connect_worker = DatabaseConnectWorker(self.current_config, self.db_type_combo.currentText())
        self.connect_worker.finished.connect(self._on_connect_finished)
        self.connect_worker.start()

    def _on_connect_finished(self, success, message, tables_json):
        """连接完成"""
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("🔌 连接数据库")

        if success:
            self.tables = json.loads(tables_json)
            self.table_list.clear()
            self.visual_table_list.clear()
            for table in self.tables:
                self.table_list.addItem(table)
                self.visual_table_list.addItem(table)
            QMessageBox.information(self, "成功", f"{message}\n\n共发现 {len(self.tables)} 张表")
        else:
            QMessageBox.warning(self, "失败", message)

    def _on_table_double_clicked(self, item):
        """双击表名获取结构"""
        table_name = item.text()
        self._fetch_table_schema(table_name)

    def _fetch_table_schema(self, table_name):
        """获取表结构"""
        if table_name in self.table_schemas:
            QMessageBox.information(self, "提示", f"表 {table_name} 结构已加载")
            return

        self.schema_worker = TableSchemaWorker(self.current_config, self.db_type_combo.currentText(), table_name)
        self.schema_worker.finished.connect(lambda s, m, d: self._on_schema_finished(s, m, d, table_name))
        self.schema_worker.start()

    def _on_schema_finished(self, success, message, schema_json, table_name):
        """获取表结构完成"""
        if success:
            self.table_schemas[table_name] = json.loads(schema_json)
            QMessageBox.information(self, "成功", f"表 {table_name} 结构已加载")
        else:
            QMessageBox.warning(self, "失败", message)

    def _save_api_key(self):
        """保存 API Key"""
        self.ai_api_key = self.api_key_edit.text().strip()
        if self.ai_api_key:
            os.environ["ANTHROPIC_API_KEY"] = self.ai_api_key
            QMessageBox.information(self, "成功", "API Key 已保存")
        else:
            QMessageBox.warning(self, "提示", "请输入 API Key")

    def _generate_sql_with_ai(self):
        """使用 AI 生成 SQL"""
        request = self.ai_request_edit.toPlainText().strip()
        if not request:
            QMessageBox.warning(self, "提示", "请输入查询需求")
            return

        if not self.ai_api_key:
            QMessageBox.warning(self, "提示", "请先配置 API Key")
            return

        # 构建表结构描述
        schema_desc = self._build_schema_description()
        if not schema_desc:
            QMessageBox.warning(self, "提示", "请先连接数据库并加载至少一个表的结构")
            return

        self.ai_gen_btn.setEnabled(False)
        self.ai_gen_btn.setText("生成中...")

        # 启动 AI 生成线程
        self.ai_worker = AISqlWorker(self.ai_api_key, schema_desc, request)
        self.ai_worker.finished.connect(self._on_ai_finished)
        self.ai_worker.start()

    def _build_schema_description(self):
        """构建表结构描述"""
        if not self.table_schemas:
            return ""

        lines = ["数据库表结构：\n"]
        for table_name, schema in self.table_schemas.items():
            lines.append(f"表名: {table_name}")
            lines.append("字段:")
            for col in schema.get("columns", []):
                key_info = f" ({col.get('key', '')})" if col.get('key') else ""
                lines.append(f"  - {col['name']}: {col['type']}{key_info}")

            # 外键关系
            fks = schema.get("foreign_keys", {})
            if fks:
                lines.append("外键关系:")
                for fk_col, fk_info in fks.items():
                    lines.append(f"  - {fk_col} -> {fk_info['table']}.{fk_info['column']}")
            lines.append("")

        return "\n".join(lines)

    def _on_ai_finished(self, success, sql, explanation):
        """AI 生成完成"""
        self.ai_gen_btn.setEnabled(True)
        self.ai_gen_btn.setText("⚡ AI 生成 SQL")

        if success:
            self.ai_sql_output.setPlainText(sql)
            if explanation:
                QMessageBox.information(self, "生成完成", explanation)
        else:
            QMessageBox.warning(self, "生成失败", sql)

    def _copy_ai_sql(self):
        """复制 AI 生成的 SQL"""
        sql = self.ai_sql_output.toPlainText()
        if sql:
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(sql)
            QMessageBox.information(self, "复制成功", "SQL 已复制到剪贴板")

    def _add_table_to_query(self, item):
        """添加表到查询"""
        table_name = item.text()
        if table_name not in self.query_state["tables"]:
            self.query_state["tables"].append(table_name)
            self._update_field_combos()
            self._refresh_join_table_combo()

    def _update_field_combos(self):
        """更新字段下拉框"""
        self.where_field_combo.clear()
        self.group_by_combo.clear()
        self.order_by_combo.clear()

        self.where_field_combo.addItem("")
        self.group_by_combo.addItem("")
        self.order_by_combo.addItem("")

        for table_name in self.query_state["tables"]:
            if table_name in self.table_schemas:
                for col in self.table_schemas[table_name].get("columns", []):
                    field = f"{table_name}.{col['name']}"
                    self.where_field_combo.addItem(field)
                    self.group_by_combo.addItem(field)
                    self.order_by_combo.addItem(field)

    def _refresh_join_table_combo(self):
        """刷新 JOIN 表下拉框"""
        self.join_table_combo.clear()
        for table_name in self.tables:
            if table_name not in self.query_state["tables"]:
                self.join_table_combo.addItem(table_name)

    def _remove_selected_field(self):
        """移除选中的字段"""
        current_row = self.selected_fields_list.currentRow()
        if current_row >= 0:
            self.selected_fields_list.takeItem(current_row)
            self.query_state["fields"].pop(current_row)

    def _add_join_condition(self):
        """添加 JOIN 条件"""
        table = self.join_table_combo.currentText()
        join_type = self.join_type_combo.currentText()

        if not table:
            return

        # 获取外键关系建议
        suggestion = self._get_join_suggestion(table)
        if suggestion:
            condition = f"{join_type} {table} ON {suggestion}"
        else:
            condition = f"{join_type} {table} ON ? = ?"

        self.query_state["joins"].append({
            "type": join_type,
            "table": table,
            "condition": condition
        })
        self.join_list.addItem(condition)

        if table not in self.query_state["tables"]:
            self.query_state["tables"].append(table)
            self._update_field_combos()

    def _get_join_suggestion(self, table):
        """获取 JOIN 条件建议"""
        for existing_table in self.query_state["tables"]:
            if existing_table in self.table_schemas:
                fks = self.table_schemas[existing_table].get("foreign_keys", {})
                for fk_col, fk_info in fks.items():
                    if fk_info["table"] == table:
                        return f"{existing_table}.{fk_col} = {table}.{fk_info['column']}"
            if table in self.table_schemas:
                fks = self.table_schemas[table].get("foreign_keys", {})
                for fk_col, fk_info in fks.items():
                    if fk_info["table"] == existing_table:
                        return f"{table}.{fk_col} = {existing_table}.{fk_info['column']}"
        return None

    def _add_where_condition(self):
        """添加 WHERE 条件"""
        field = self.where_field_combo.currentText()
        op = self.where_op_combo.currentText()
        value = self.where_value_edit.text().strip()

        if not field:
            return

        if op in ("IS NULL", "IS NOT NULL"):
            condition = f"{field} {op}"
        elif op == "LIKE":
            condition = f"{field} LIKE '%{value}%'"
        elif op == "IN":
            condition = f"{field} IN ({value})"
        else:
            condition = f"{field} {op} '{value}'"

        self.query_state["where"].append(condition)
        self.where_list.addItem(condition)
        self.where_value_edit.clear()

    def _generate_visual_sql(self):
        """根据可视化配置生成 SQL"""
        if not self.query_state["tables"]:
            QMessageBox.warning(self, "提示", "请先添加表")
            return

        # 获取选中的字段
        fields = []
        for i in range(self.selected_fields_list.count()):
            fields.append(self.selected_fields_list.item(i).text())

        if not fields:
            # 默认选择所有字段
            for table in self.query_state["tables"]:
                if table in self.table_schemas:
                    for col in self.table_schemas[table].get("columns", []):
                        fields.append(f"{table}.{col['name']}")

        # 构建 SQL
        sql_parts = ["SELECT"]

        # 字段
        if fields:
            sql_parts.append("    " + ",\n    ".join(fields))
        else:
            sql_parts.append("    *")

        # FROM
        sql_parts.append(f"FROM `{self.query_state['tables'][0]}`")

        # JOIN
        for join in self.query_state["joins"]:
            sql_parts.append(f"{join['type']} `{join['table']}` ON ...")

        # WHERE
        if self.query_state["where"]:
            sql_parts.append("WHERE " + " AND ".join(self.query_state["where"]))

        # GROUP BY
        group_by = self.group_by_combo.currentText()
        if group_by:
            sql_parts.append(f"GROUP BY {group_by}")

        # ORDER BY
        order_by = self.order_by_combo.currentText()
        if order_by:
            order_dir = self.order_dir_combo.currentText()
            sql_parts.append(f"ORDER BY {order_by} {order_dir}")

        # LIMIT
        limit = self.limit_spin.value()
        if limit < 100000:
            sql_parts.append(f"LIMIT {limit}")

        sql = " ".join(sql_parts) + ";"
        self.visual_sql_output.setPlainText(sql)

    def _copy_visual_sql(self):
        """复制可视化生成的 SQL"""
        sql = self.visual_sql_output.toPlainText()
        if sql:
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(sql)
            QMessageBox.information(self, "复制成功", "SQL 已复制到剪贴板")

    def _export_sql(self):
        """导出 SQL 文件"""
        sql = self.visual_sql_output.toPlainText() or self.ai_sql_output.toPlainText()
        if not sql:
            QMessageBox.warning(self, "提示", "没有可导出的 SQL")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出 SQL 文件", "", "SQL 文件 (*.sql);;所有文件 (*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(sql)
                QMessageBox.information(self, "导出成功", f"SQL 已导出到:\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "导出失败", f"导出失败: {str(e)}")


class AISqlWorker(QThread):
    """AI SQL 生成工作线程"""
    finished = Signal(bool, str, str)  # success, sql, explanation

    def __init__(self, api_key, schema_desc, request):
        super().__init__()
        self.api_key = api_key
        self.schema_desc = schema_desc
        self.request = request

    def run(self):
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            prompt = f"""你是一个 SQL 专家。根据以下数据库表结构和用户需求，生成对应的 SQL 查询语句。

{self.schema_desc}

用户需求：{self.request}

请生成 SQL 查询语句，并简要解释你的查询逻辑。只返回 SQL 和解释，不要其他内容。

SQL:"""

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response = message.content[0].text

            # 分离 SQL 和解释
            if "解释" in response or "说明" in response or "Explanation" in response:
                parts = response.split("\n\n", 1)
                sql = parts[0].strip()
                explanation = parts[1].strip() if len(parts) > 1 else ""
            else:
                sql = response.strip()
                explanation = "SQL 已生成"

            # 清理 SQL
            sql = sql.replace("```sql", "").replace("```", "").strip()

            self.finished.emit(True, sql, explanation)

        except ImportError:
            self.finished.emit(False, "请先安装 anthropic 库: pip install anthropic", "")
        except Exception as e:
            self.finished.emit(False, f"AI 生成失败: {str(e)}", "")
