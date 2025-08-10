import os
from playwright_controller.base_module import BaseModule
from common.read_data import read_yaml
from playwright.sync_api import sync_playwright


class BrowserController(BaseModule):
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.context = None
        self.config = read_yaml("config.yaml")

    def run_method_by_name(self, name):
        method = getattr(self, name, None)
        if callable(method):
            return method()
        else:
            raise Exception(f"未找到方法: {name}")

    def load_url(self, url):
        self.page.goto(url)

    def refresh(self):
        if self.page:
            self.page.reload()

    def execute_code(self, code, globals_dict):
        if self.page is None:
            raise Exception("Target page, context or browser has been closed")
        exec(code, globals_dict)

    def close_browser(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.browser = None
        self.context = None
        self.page = None
        return "浏览器已关闭"

    def start_browser(self):
        # 如果浏览器还在运行，先关闭再启动
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass
            try:
                self.playwright.stop()
            except Exception:
                pass
            self.browser = None
            self.context = None
            self.page = None

        # 重新启动
        self.playwright = sync_playwright().start()

        # 指定用户数据目录（持久化）
        user_data_dir = os.path.join(os.getcwd(), "userdata")
        self.browser = self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            args=["--start-maximized"]
        )

        self.context = self.browser
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()

        self.page.set_default_timeout(self.config["timeout"]["action_timeout"])  # 元素操作相关超时
        self.page.set_default_navigation_timeout(self.config["timeout"]["page_timeout"])  # 页面跳转相关超时
        return "浏览器初始化完成"

browser_controller = BrowserController()
