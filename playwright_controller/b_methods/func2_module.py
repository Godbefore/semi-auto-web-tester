from playwright_controller.methods_registry import register_method
from playwright_controller.base_module import BaseModule

class Func2Module(BaseModule):

    @register_method("打开bing", category="Bing", order=1)
    def open_bing(self):
        self.page.goto("https://www.bing.com/?mkt=zh-CN")
