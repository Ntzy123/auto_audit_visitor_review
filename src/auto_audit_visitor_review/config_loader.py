# config_loader.py - 配置管理（config.toml）

import os
import sys
import urllib.parse

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        print("[config] 请安装 tomli: pip install tomli")
        sys.exit(1)

CONFIG_FILE = "config.toml"

DEFAULT_CONTENT = """# 访客审核自动化 - 人员配置
# 选择使用第几组参数启动
current_user = 1

[[users]]
id = 1
phone = "18208475905"
name = "花梦莲"
uid = "2462900"
project_code = "52010017"

[[users]]
id = 2
phone = "18085009482"
name = "李海波"
uid = "1702071"
project_code = "52010017"
"""


def _project_root():
    """返回项目根目录（包含 src/ 的目录）。"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ensure_config():
    """确保 config.toml 存在于项目根目录，不存在则释放默认配置。"""
    path = os.path.join(_project_root(), CONFIG_FILE)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_CONTENT.lstrip("\n"))
        print(f"[config] 已生成默认配置文件: {path}")
    return path


def load_config():
    """加载 config.toml，返回当前组参数字典。"""
    path = ensure_config()
    with open(path, "rb") as f:
        data = tomllib.load(f)

    current_user = data.get("current_user", 1)
    users = data.get("users", [])

    group = next((g for g in users if g.get("id") == current_user), None)
    if group is None and users:
        group = users[0]
    if group is None:
        print("[config] 配置文件中没有有效的人员信息")
        sys.exit(1)

    return {
        "phone": group["phone"],
        "name": group["name"],
        "uid": str(group["uid"]),
        "project_code": str(group["project_code"]),
    }


BASE_URL = "https://peoplego.vankeservice.com/#/Embed/visitorReview/pending"


def build_url(config):
    """根据配置参数构建完整 URL。"""
    query = urllib.parse.urlencode({
        "phone": config["phone"],
        "name": config["name"],
        "id": config["uid"],
        "projectCode": config["project_code"],
    })
    return f"{BASE_URL}&{query}"
