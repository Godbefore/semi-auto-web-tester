from common.read_data import read_yaml
from playwright.sync_api import Page


class BaseModule:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page:Page|None = None
        self.context = None
        self._config_path = "config.yaml"  # 存储路径以便复用

    @property
    def config(self):
        """动态读取YAML文件，确保每次获取最新配置"""
        return read_yaml(self._config_path)
