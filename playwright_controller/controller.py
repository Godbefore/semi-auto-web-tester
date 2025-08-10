import importlib
import os
import pkgutil

from playwright.sync_api import sync_playwright


class BrowserController:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    def run_method_by_name(self, name):
        method = getattr(self, name, None)
        if callable(method):
            return method()
        else:
            raise Exception(f"未找到方法: {name}")

    # ======================
    # 基础封装方法
    # ======================
    def load_url(self, url):
        page = self.start_browser()
        page.goto(url)

    def refresh(self):
        if self.page:
            self.page.reload()

    # ======================
    # 代码执行
    # ======================
    def execute_code(self, code, globals_dict):
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

        self.page.set_default_timeout(15000)  # 元素操作相关超时
        self.page.set_default_navigation_timeout(30000)  # 页面跳转相关超时
        return "浏览器已重启"

browser_controller = BrowserController()
