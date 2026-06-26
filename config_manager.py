import json
import csv
import os

CONFIG_FILE = "config.json"
SERVICES_FILE = "services.csv"

SERVICES_HEADERS = [
    "service_name", "ssh_host", "ssh_user", "local_jar_path",
    "remote_jar_dir", "compose_dir", "compose_service_name",
    "remote_log_path", "local_log_dir"
]


def get_app_dir():
    if getattr(__import__('sys'), 'frozen', False):
        return os.path.dirname(__import__('sys').executable)
    return os.path.dirname(os.path.abspath(__file__))


def config_path():
    return os.path.join(get_app_dir(), CONFIG_FILE)


def services_path():
    return os.path.join(get_app_dir(), SERVICES_FILE)


def load_config():
    path = config_path()
    defaults = {
        "default_ssh_host": "",
        "default_ssh_user": "",
        "default_ssh_port": 22,
        "auth_method": "key",
        "ssh_key_path": "",
        "ssh_password": ""
    }
    if not os.path.exists(path):
        save_config(defaults)
        return defaults
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    for k, v in defaults.items():
        cfg.setdefault(k, v)
    return cfg


def save_config(cfg):
    path = config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=4)


def load_services():
    path = services_path()
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(SERVICES_HEADERS)
        return []
    services = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("service_name", "").strip():
                services.append(row)
    return services


def save_services(services):
    path = services_path()
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SERVICES_HEADERS)
        writer.writeheader()
        writer.writerows(services)
