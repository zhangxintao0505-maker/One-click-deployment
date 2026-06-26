# One-click-deployment
Windows 桌面端部署管理工具
# 提示词：Windows 桌面端部署管理工具

请基于以下需求，开发一个 **Windows 桌面应用**，作为远程服务部署的可视化操作面板，实现三大功能：
1. 将本地 jar 包上传到服务器指定目录
2. 在服务器上执行 docker-compose 重启对应服务
3. 将服务器上的日志文件/目录下载到本地指定目录

## 1. 技术栈（请按此实现，不要使用需要额外命令行工具的方案）

- **语言/框架**：Python 3 + PySide6（Qt for Python）做桌面GUI
- **SSH/SFTP**：使用 `paramiko` 库直接实现 SSH 命令执行与 SFTP 文件传输，**不要依赖系统自带的 ssh / scp / rsync / docker-compose 命令行工具**，因为目标用户是 Windows 桌面用户，未必安装这些工具
- **打包**：最终使用 PyInstaller 打包成单个 `.exe`（`--onefile --windowed`），提供打包命令和说明
- **后台执行**：所有网络/SSH操作必须放在 `QThread`（或 `QRunnable` + `QThreadPool`）中执行，通过 Qt 信号（signal）把执行进度/日志实时发回主线程更新UI，避免界面卡死

## 2. 配置文件设计

### 2.1 服务列表配置 `services.csv`
使用 CSV 格式（UTF-8编码），每行一个服务，字段固定为以下9个（含表头注释行）：

```
service_name, ssh_host, ssh_user, local_jar_path, remote_jar_dir,
compose_dir, compose_service_name, remote_log_path, local_log_dir
```

- `local_jar_path` / `local_log_dir` 在Windows上是本地路径（如 `D:\deploy\jars\xxx.jar`、`D:\deploy\logs\xxx`）
- `ssh_host` / `ssh_user` 留空表示使用全局默认配置
- 应用启动时自动读取并解析该文件，展示为服务列表；如文件不存在则提示用户新建

### 2.2 全局默认配置 `config.json`
```json
{
  "default_ssh_host": "192.168.1.100",
  "default_ssh_user": "deploy",
  "default_ssh_port": 22,
  "auth_method": "key",            // "key" 或 "password"
  "ssh_key_path": "C:\\Users\\xxx\\.ssh\\id_rsa",
  "ssh_password": ""                 // 仅当 auth_method=="password" 时使用
}
```

### 2.3 配置管理界面
- 提供一个"设置"页面/对话框，可编辑 `config.json` 中的字段，保存即写回文件
- 提供一个"服务管理"页面，以表格形式展示/新增/编辑/删除 `services.csv` 中的每一行，支持本地路径用文件/文件夹选择对话框填写（`QFileDialog`）

## 3. 核心功能实现（均通过 paramiko 实现，需要在子线程中执行）

### 3.1 上传 Jar 包
1. 建立 SSHClient 连接（支持私钥或密码两种认证方式）
2. 通过 SFTP 检查/递归创建 `remote_jar_dir`（远程目录不存在则逐级 mkdir）
3. 用 `sftp.put(local_path, remote_path, callback=...)` 上传，`callback` 用于回调更新进度条（已传输字节数/总字节数）
4. 上传完成后关闭连接，发送完成信号

### 3.2 重启 docker-compose 服务
1. 通过 `ssh.exec_command()` 执行命令：
   ```bash
   cd '<compose_dir>' && (docker compose restart <compose_service_name> || docker-compose restart <compose_service_name>)
   ```
2. 实时循环读取 `stdout`/`stderr` 的 channel，逐行通过信号发送到UI日志区域
3. 获取命令退出码，判断成功/失败并在UI显示明确状态

### 3.3 下载日志
1. 通过 SFTP 判断 `remote_log_path` 是文件还是目录（`sftp.stat` 判断 `st_mode`）
2. 如果是文件：直接 `sftp.get()` 下载到 `local_log_dir`
3. 如果是目录：递归遍历 `sftp.listdir_attr()`，在本地创建对应目录结构后逐个下载文件，并实时显示当前下载进度（第几个文件/共几个）
4. 提供一个勾选项"按时间戳归档"：勾选后在 `local_log_dir` 下创建 `YYYYMMDD_HHMMSS` 子目录再下载

### 3.4 一键执行
依次执行 3.1 -> 3.2 -> 3.3，任一步失败立即停止并在UI明确标红显示失败步骤，已完成步骤标绿

## 4. 界面设计

主窗口布局建议（左右分栏）：
- **左侧**：服务列表（QListWidget 或 QTableWidget），点击选中某个服务后右侧显示其详细信息（服务器地址、compose目录、日志路径等）
- **右上**：操作按钮区——"上传Jar"、"重启服务"、"下载日志"（旁边带"按时间戳归档"勾选框）、"一键全部执行"，执行中按钮禁用并显示loading状态
- **右下**：实时日志输出区（QTextEdit，只读，黑底白字/终端风格，自动滚动到底部），支持"清空日志"按钮
- **顶部菜单/工具栏**：设置（编辑config.json）、服务管理（编辑services.csv）、关于

状态反馈：
- 每步操作完成后用颜色/图标（✅ 成功 / ❌ 失败 / ⏳ 进行中）明确提示
- 操作历史：维护一个内存列表（最近20条），记录时间、服务名、动作、结果，可在一个简单的"历史"面板查看

## 5. 错误处理与连接管理

- SSH连接失败（超时、认证失败、主机不可达）需捕获异常并在日志区显示清晰的中文错误提示，不能让程序崩溃
- 每次操作使用独立的SSH连接，操作结束后正确关闭（`sftp.close()` / `ssh.close()`），避免连接泄漏
- 设置合理的连接超时（如10秒）和命令执行超时

## 6. 安全注意事项（请在代码注释/README中说明）

- 推荐使用 SSH 私钥认证而非密码；如使用密码认证，`config.json` 中的密码以明文保存，需在README中提示用户注意文件权限，或建议改用密钥
- 私钥路径选择使用 `QFileDialog`，不要将私钥内容复制到程序目录

## 7. 项目结构建议

```
deploy-desktop/
├── main.py              # 程序入口，初始化主窗口
├── ssh_worker.py         # SSH/SFTP操作的QThread实现（上传/重启/下载）
├── config_manager.py     # 读写 config.json 和 services.csv
├── ui/
│   ├── main_window.py
│   ├── settings_dialog.py
│   └── services_dialog.py
├── config.json
├── services.csv
├── requirements.txt       # PySide6, paramiko
└── README.md              # 安装依赖、运行、打包exe的说明
```

## 8. 交付要求

1. 完整可运行的源代码（按上述结构组织）
2. `requirements.txt`
3. `README.md`，包含：
   - 安装依赖：`pip install -r requirements.txt`
   - 运行：`python main.py`
   - 打包exe命令：`pyinstaller --onefile --windowed main.py`，并说明打包后如何携带 `config.json`/`services.csv`（建议放在exe同目录，程序读取exe所在目录而非临时解压目录）
4. 示例 `config.json` 和 `services.csv`（含1-2条示例服务）

---

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行
```bash
python main.py
```

### 打包为 exe
```bash
pyinstaller --onefile --windowed --name DeployTool main.py
```

打包后将 `config.json` 和 `services.csv` 放在生成的 `.exe` 同目录下，程序会自动读取该目录的配置文件。

### 安全提示
- 推荐使用 SSH 私钥认证，避免在 `config.json` 中明文保存密码
- 如使用密码认证，请注意 `config.json` 文件的访问权限
- 私钥路径通过文件选择对话框填写，程序不会复制私钥内容
