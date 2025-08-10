from playwright_controller.methods_registry import register_method
from playwright_controller.base_module import BaseModule


class Func1Module(BaseModule):

    @register_method("打开github", category="Github", order=1)
    def open_github(self):
        self.page.goto("https://www.github.com/")

    @register_method("然后在github中搜索", category="Github", order=2)
    def search_github(self):
        self.page.get_by_placeholder("Search or jump to...").click()
        search_input = self.page.locator("#query-builder-test")
        search_input.fill("Godbefore")  # 直接填充内容
        search_input.press("Enter")
