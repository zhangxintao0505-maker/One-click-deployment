import os
import stat
import paramiko
from PySide6.QtCore import QThread, Signal


def create_ssh_client(host, port, user, auth_method, key_path, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connect_kwargs = {
        "hostname": host,
        "port": port,
        "username": user,
        "timeout": 10,
    }
    if auth_method == "key" and key_path:
        connect_kwargs["key_filename"] = key_path
    else:
        connect_kwargs["password"] = password
    ssh.connect(**connect_kwargs)
    return ssh


class UploadWorker(QThread):
    log = Signal(str)
    progress = Signal(int, int)
    finished_ok = Signal(bool, str)

    def __init__(self, config, service):
        super().__init__()
        self.config = config
        self.service = service

    def run(self):
        try:
            host = self.service.get("ssh_host", "").strip() or self.config["default_ssh_host"]
            user = self.service.get("ssh_user", "").strip() or self.config["default_ssh_user"]
            port = int(self.config.get("default_ssh_port", 22))
            local_path = self.service["local_jar_path"]
            remote_dir = self.service["remote_jar_dir"]

            if not os.path.exists(local_path):
                self.log.emit(f"❌ 本地文件不存在: {local_path}")
                self.finished_ok.emit(False, "本地文件不存在")
                return

            self.log.emit(f"正在连接 {host} ...")
            ssh = create_ssh_client(
                host, port, user,
                self.config["auth_method"],
                self.config.get("ssh_key_path", ""),
                self.config.get("ssh_password", "")
            )
            self.log.emit("SSH 连接成功")

            sftp = ssh.open_sftp()
            self._ensure_remote_dir(sftp, remote_dir)

            filename = os.path.basename(local_path)
            remote_path = remote_dir.rstrip("/") + "/" + filename
            total_size = os.path.getsize(local_path)
            self.log.emit(f"开始上传 {filename} ({total_size} 字节) -> {remote_path}")

            transferred = [0]
            def callback(bytes_transferred, total):
                transferred[0] = bytes_transferred
                self.progress.emit(bytes_transferred, total)

            sftp.put(local_path, remote_path, callback=callback)
            self.log.emit(f"✅ 上传完成: {remote_path}")

            sftp.close()
            ssh.close()
            self.finished_ok.emit(True, "上传成功")
        except Exception as e:
            self.log.emit(f"❌ 上传失败: {e}")
            self.finished_ok.emit(False, str(e))

    def _ensure_remote_dir(self, sftp, remote_dir):
        parts = remote_dir.strip("/").split("/")
        current = ""
        for part in parts:
            current += "/" + part
            try:
                sftp.stat(current)
            except FileNotFoundError:
                self.log.emit(f"创建远程目录: {current}")
                sftp.mkdir(current)


class RestartWorker(QThread):
    log = Signal(str)
    finished_ok = Signal(bool, str)

    def __init__(self, config, service):
        super().__init__()
        self.config = config
        self.service = service

    def run(self):
        try:
            host = self.service.get("ssh_host", "").strip() or self.config["default_ssh_host"]
            user = self.service.get("ssh_user", "").strip() or self.config["default_ssh_user"]
            port = int(self.config.get("default_ssh_port", 22))
            compose_dir = self.service["compose_dir"]
            compose_service = self.service["compose_service_name"]

            self.log.emit(f"正在连接 {host} ...")
            ssh = create_ssh_client(
                host, port, user,
                self.config["auth_method"],
                self.config.get("ssh_key_path", ""),
                self.config.get("ssh_password", "")
            )
            self.log.emit("SSH 连接成功")

            cmd = (
                f"cd '{compose_dir}' && "
                f"(docker compose restart {compose_service} || "
                f"docker-compose restart {compose_service})"
            )
            self.log.emit(f"执行命令: {cmd}")

            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
            channel = stdout.channel

            while not channel.exit_status_ready():
                if channel.recv_ready():
                    line = channel.recv(1024).decode("utf-8", errors="replace")
                    for l in line.splitlines():
                        self.log.emit(l)
                if channel.recv_stderr_ready():
                    line = channel.recv_stderr(1024).decode("utf-8", errors="replace")
                    for l in line.splitlines():
                        self.log.emit(f"[stderr] {l}")

            exit_code = channel.recv_exit_status()
            remaining_out = stdout.read().decode("utf-8", errors="replace")
            remaining_err = stderr.read().decode("utf-8", errors="replace")
            for l in remaining_out.splitlines():
                self.log.emit(l)
            for l in remaining_err.splitlines():
                self.log.emit(f"[stderr] {l}")

            ssh.close()

            if exit_code == 0:
                self.log.emit("✅ 服务重启成功")
                self.finished_ok.emit(True, "重启成功")
            else:
                self.log.emit(f"❌ 服务重启失败 (退出码: {exit_code})")
                self.finished_ok.emit(False, f"退出码: {exit_code}")
        except Exception as e:
            self.log.emit(f"❌ 重启失败: {e}")
            self.finished_ok.emit(False, str(e))


class DownloadWorker(QThread):
    log = Signal(str)
    progress = Signal(int, int)
    finished_ok = Signal(bool, str)

    def __init__(self, config, service, archive=False):
        super().__init__()
        self.config = config
        self.service = service
        self.archive = archive

    def run(self):
        try:
            host = self.service.get("ssh_host", "").strip() or self.config["default_ssh_host"]
            user = self.service.get("ssh_user", "").strip() or self.config["default_ssh_user"]
            port = int(self.config.get("default_ssh_port", 22))
            remote_path = self.service["remote_log_path"]
            local_dir = self.service["local_log_dir"]

            self.log.emit(f"正在连接 {host} ...")
            ssh = create_ssh_client(
                host, port, user,
                self.config["auth_method"],
                self.config.get("ssh_key_path", ""),
                self.config.get("ssh_password", "")
            )
            self.log.emit("SSH 连接成功")

            sftp = ssh.open_sftp()

            if self.archive:
                import datetime
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                local_dir = os.path.join(local_dir, ts)

            os.makedirs(local_dir, exist_ok=True)

            try:
                st = sftp.stat(remote_path)
            except FileNotFoundError:
                self.log.emit(f"❌ 远程路径不存在: {remote_path}")
                sftp.close()
                ssh.close()
                self.finished_ok.emit(False, "远程路径不存在")
                return

            if stat.S_ISDIR(st.st_mode):
                self._download_dir(sftp, remote_path, local_dir)
            else:
                filename = os.path.basename(remote_path)
                dest = os.path.join(local_dir, filename)
                self.log.emit(f"下载文件: {remote_path} -> {dest}")
                total = st.st_size
                sftp.get(remote_path, dest, callback=lambda c, t: self.progress.emit(c, t))
                self.log.emit(f"✅ 下载完成: {dest}")

            sftp.close()
            ssh.close()
            self.finished_ok.emit(True, "下载成功")
        except Exception as e:
            self.log.emit(f"❌ 下载失败: {e}")
            self.finished_ok.emit(False, str(e))

    def _download_dir(self, sftp, remote_dir, local_dir):
        items = sftp.listdir_attr(remote_dir)
        total_files = []
        self._collect_files(sftp, remote_dir, total_files)
        self.log.emit(f"目录包含 {len(total_files)} 个文件")

        downloaded = [0]
        self._do_download(sftp, remote_dir, local_dir, total_files, downloaded)

    def _collect_files(self, sftp, remote_dir, file_list):
        for item in sftp.listdir_attr(remote_dir):
            remote_path = remote_dir.rstrip("/") + "/" + item.filename
            if stat.S_ISDIR(item.st_mode):
                self._collect_files(sftp, remote_path, file_list)
            else:
                file_list.append(remote_path)

    def _do_download(self, sftp, remote_dir, local_dir, total_files, downloaded):
        for item in sftp.listdir_attr(remote_dir):
            remote_path = remote_dir.rstrip("/") + "/" + item.filename
            local_path = os.path.join(local_dir, item.filename)
            if stat.S_ISDIR(item.st_mode):
                os.makedirs(local_path, exist_ok=True)
                self._do_download(sftp, remote_path, local_path, total_files, downloaded)
            else:
                downloaded[0] += 1
                idx = downloaded[0]
                total = len(total_files)
                self.log.emit(f"[{idx}/{total}] 下载: {item.filename}")
                sftp.get(remote_path, local_path)
                self.progress.emit(idx, total)
